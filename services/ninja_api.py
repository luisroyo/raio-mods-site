import json
import os
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import socket

@dataclass
class NinjaApiError(Exception):
    status: Optional[int]
    message: str
    errors: Optional[Dict[str, List[str]]] = None
    idempotency_key: Optional[str] = None

    def __str__(self) -> str:
        status = str(self.status) if self.status is not None else "network"
        retry_key = f" Idempotency-Key: {self.idempotency_key}." if self.idempotency_key else ""
        return f"Ninja API error ({status}): {self.message}.{retry_key}"

class NinjaSellerApi:
    def __init__(self, base_url: str = None, token: str = None, timeout_seconds: int = 20) -> None:
        env_token = os.environ.get("NINJA_API_TOKEN")
        env_url = os.environ.get("NINJA_API_BASE_URL", "https://ninja-engine.net/api/v1/seller-api")
        
        self.base_url = (base_url or env_url).rstrip("/")
        self.token = token or env_token
        self.timeout_seconds = timeout_seconds

        if not self.token:
            print("[NinjaSellerApi] AVISO: NINJA_API_TOKEN não configurado no ambiente")

    def _request_json(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        max_attempts: int = 5,
    ) -> Dict[str, Any]:
        
        if not self.token:
            raise NinjaApiError(None, "NINJA_API_TOKEN is not set.")

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "Mozilla/5.0",
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
                    # Sometimes DELETE might not return body, handle it safely
                    response_bytes = response.read()
                    if not response_bytes:
                        return {}
                    return json.loads(response_bytes.decode("utf-8"))
            except HTTPError as error:
                payload = self._error_payload(error)
                message = str(payload.get("message", "Request failed"))
                errors = payload.get("errors")

                if error.code == 429:
                    wait_seconds = self._retry_after(error)
                    if attempt < max_attempts:
                        time.sleep(wait_seconds)
                        continue
                    raise NinjaApiError(
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
                    raise NinjaApiError(
                        409,
                        "The original request is still running; retry it unchanged",
                        errors,
                        idempotency_key,
                    ) from error

                if 500 <= error.code < 600 and attempt < max_attempts:
                    time.sleep(min(2 ** (attempt - 1), 8))
                    continue

                raise NinjaApiError(
                    error.code,
                    message,
                    errors if isinstance(errors, dict) else None,
                    idempotency_key,
                ) from error

            except (URLError, TimeoutError, socket.timeout) as error:
                if attempt < max_attempts:
                    time.sleep(min(2 ** (attempt - 1), 8))
                    continue
                raise NinjaApiError(
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

    @staticmethod
    def new_intended_action_key() -> str:
        return str(uuid.uuid4())

    def create_customer(
        self,
        username: str,
        password: str,
        game: str,
        mode: str,
        duration_seconds: int,
        display_name: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        POST /customers
        Create customer access.
        """
        if idempotency_key is None:
            idempotency_key = self.new_intended_action_key()
            
        body = {
            "username": username,
            "password": password,
            "display_name": display_name,
            "game": game,
            "mode": mode,
            "duration_seconds": duration_seconds
        }
        
        return self._request_json(
            "POST",
            "/customers",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_customer(
        self,
        username: str,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        DELETE /customers/:username
        Delete an owned customer.
        """
        if idempotency_key is None:
            idempotency_key = self.new_intended_action_key()
            
        return self._request_json(
            "DELETE",
            f"/customers/{username}",
            idempotency_key=idempotency_key,
        )

    def reset_device(
        self,
        username: str,
        game: str,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        POST /customers/:username/device-reset
        Reset customer device.
        """
        if idempotency_key is None:
            idempotency_key = self.new_intended_action_key()
            
        body = {
            "game": game
        }
        
        return self._request_json(
            "POST",
            f"/customers/{username}/device-reset",
            body=body,
            idempotency_key=idempotency_key,
        )
