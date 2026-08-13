import json
import os
import socket
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

@dataclass
class SellerApiError(Exception):
    status: Optional[int]
    message: str
    errors: Optional[Dict[str, List[str]]] = None
    idempotency_key: Optional[str] = None

    def __str__(self) -> str:
        status = str(self.status) if self.status is not None else "network"
        retry_key = (
            f" Idempotency-Key: {self.idempotency_key}."
            if self.idempotency_key
            else ""
        )
        return f"Seller API error ({status}): {self.message}.{retry_key}"


class KosSellerApi:
    def __init__(self, base_url: str = None, token: str = None, timeout_seconds: int = 20) -> None:
        # Pega do .env
        env_token = os.environ.get("KOS_API_TOKEN")
        env_url = os.environ.get("KOS_API_BASE_URL", "https://koscheat.xyz/api/v1")
        
        self.base_url = (base_url or env_url).rstrip("/")
        self.token = token or env_token
        self.timeout_seconds = timeout_seconds

        if not self.token:
            print("[KosSellerApi] AVISO: KOS_API_TOKEN não configurado no ambiente")

    def _request_json(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        max_attempts: int = 5,
    ) -> Dict[str, Any]:
        
        if not self.token:
            raise SellerApiError(None, "KOS_API_TOKEN is not set.")

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        }
        encoded_body = None

        if body is not None:
            headers["Content-Type"] = "application/json"
            encoded_body = json.dumps(body).encode("utf-8")

        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key

        for attempt in range(1, max_attempts + 1):
            request = Request(
                url=f"{self.base_url}{path}",
                data=encoded_body,
                headers=headers,
                method=method,
            )

            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                payload = self._error_payload(error)
                message = str(payload.get("message", "Request failed"))
                errors = payload.get("errors")

                if error.code == 429:
                    wait_seconds = self._retry_after(error)
                    if attempt < max_attempts:
                        time.sleep(wait_seconds)
                        continue
                    raise SellerApiError(
                        429,
                        f"Rate limit exceeded; retry after {wait_seconds} seconds",
                        errors,
                        idempotency_key,
                    ) from error

                if error.code == 409 and "still in progress" in message.lower():
                    wait_seconds = self._retry_after(error)
                    if attempt < max_attempts:
                        time.sleep(wait_seconds)
                        continue
                    raise SellerApiError(
                        409,
                        "The original request is still running; retry it unchanged",
                        errors,
                        idempotency_key,
                    ) from error

                if error.code == 401:
                    message = "Token missing, invalid, or revoked; obtain a valid token"
                elif error.code == 403:
                    message = f"Permission or account restriction: {message}"
                elif error.code == 404:
                    message = "Key not found or not owned by this seller"
                elif error.code == 409:
                    message = (
                        "This idempotency key represents a different request; "
                        "use a fresh key only for a genuinely new intended action"
                    )
                elif error.code == 422:
                    message = f"Validation/Balance error: {message}"
                
                if 500 <= error.code < 600 and attempt < max_attempts:
                    time.sleep(min(2 ** (attempt - 1), 8))
                    continue

                raise SellerApiError(
                    error.code,
                    message,
                    errors if isinstance(errors, dict) else None,
                    idempotency_key,
                ) from error

            except (URLError, TimeoutError, socket.timeout) as error:
                if attempt < max_attempts:
                    time.sleep(min(2 ** (attempt - 1), 8))
                    continue
                raise SellerApiError(
                    None,
                    "No response received; retry the same intended action with the same key",
                    idempotency_key=idempotency_key,
                ) from error

        raise RuntimeError("Unreachable retry state")

    @staticmethod
    def _error_payload(error: HTTPError) -> Dict[str, Any]:
        try:
            payload = json.loads(error.read().decode("utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _retry_after(error: HTTPError) -> int:
        try:
            return max(1, int(error.headers.get("Retry-After", "1")))
        except (TypeError, ValueError):
            return 1

    def get_key(self, key_id: int, key_system: str) -> Dict[str, Any]:
        query = urlencode({"key_system": key_system})
        return self._request_json("GET", f"/keys/{key_id}?{query}")["data"]

    def generate_keys(
        self,
        game_type: str,
        duration: int,
        quantity: int,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        return self._request_json(
            "POST",
            "/keys",
            {
                "game_type": game_type,
                "duration": int(duration),
                "quantity": int(quantity),
            },
            idempotency_key,
        )["data"]

    def reset_key(
        self,
        key_id: int,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        return self._request_json(
            "POST",
            f"/keys/{key_id}/reset",
            {"key_system": "direct-license"},
            idempotency_key,
        )["data"]

    def delete_key(
        self,
        key_id: int,
        key_system: str,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        return self._request_json(
            "DELETE",
            f"/keys/{key_id}",
            {"key_system": key_system},
            idempotency_key,
        )["data"]

    @staticmethod
    def new_intended_action_key() -> str:
        return str(uuid.uuid4())
