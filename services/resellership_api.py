import json
import os
import secrets
import socket
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass
class ResellershipApiError(Exception):
    status: Optional[int]
    message: str
    code: Optional[str] = None
    correlation_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    raw_payload: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        status_str = str(self.status) if self.status is not None else "network"
        code_str = f" [{self.code}]" if self.code else ""
        corr_str = f" CorrelationId: {self.correlation_id}." if self.correlation_id else ""
        retry_key = f" Idempotency-Key: {self.idempotency_key}." if self.idempotency_key else ""
        return f"Resellership API error ({status_str}{code_str}): {self.message}.{corr_str}{retry_key}"


class ResellershipApi:
    """
    Cliente para integração com a Resellership API (v1).
    Documentação: https://resellership.art/api/v1
    """

    DEFAULT_BASE_URL = "https://resellership.art/api/v1"

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: int = 25,
    ) -> None:
        env_key = os.environ.get("RESELLERSHIP_API_KEY") or os.environ.get("RESELLERSHIP_API_TOKEN")
        env_url = os.environ.get("RESELLERSHIP_API_BASE_URL", self.DEFAULT_BASE_URL)

        self.base_url = (base_url or env_url).rstrip("/")
        self.api_key = (api_key or env_key or "").strip()
        self.timeout_seconds = timeout_seconds

        if not self.api_key:
            print("[ResellershipApi] AVISO: RESELLERSHIP_API_KEY não configurada no ambiente (.env)")

    def _format_endpoint(self, path: str) -> str:
        clean = path.strip().lstrip("/")
        if "?" in clean:
            base, query = clean.split("?", 1)
            if not base.endswith(".php"):
                base = f"{base}.php"
            return f"{self.base_url}/{base}?{query}"
        if not clean.endswith(".php"):
            clean = f"{clean}.php"
        return f"{self.base_url}/{clean}"

    def _request_json(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        is_write: bool = False,
        max_attempts: int = 5,
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ResellershipApiError(
                None,
                "RESELLERSHIP_API_KEY is not configured.",
                code="CONFIG_ERROR"
            )

        url = self._format_endpoint(path)
        encoded_body = None
        if body is not None:
            encoded_body = json.dumps(body).encode("utf-8")

        for attempt in range(1, max_attempts + 1):
            headers = {
                "Accept": "application/json",
                "X-Api-Key": self.api_key,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            }
            if encoded_body is not None:
                headers["Content-Type"] = "application/json"

            # Requisições de escrita (ex: criação de pedidos) requerem timestamp, nonce e idempotência
            if is_write or method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
                headers["X-Timestamp"] = str(int(time.time()))
                headers["X-Nonce"] = secrets.token_hex(16)  # 32 caracteres hexadecimais únicos
                if idempotency_key:
                    headers["Idempotency-Key"] = str(idempotency_key)

            request = Request(
                url=url,
                data=encoded_body,
                headers=headers,
                method=method.upper(),
            )

            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    response_bytes = response.read()
                    if not response_bytes:
                        return {}
                    return json.loads(response_bytes.decode("utf-8"))

            except HTTPError as error:
                payload = self._error_payload(error)
                err_obj = payload.get("error") if isinstance(payload.get("error"), dict) else {}
                err_code = err_obj.get("code") or payload.get("code")
                err_msg = err_obj.get("message") or payload.get("message") or str(error)
                corr_id = payload.get("correlationId")

                # 429 - Rate Limit Exceeded
                if error.code == 429:
                    wait_seconds = self._retry_after(error)
                    if attempt < max_attempts:
                        time.sleep(wait_seconds)
                        continue
                    raise ResellershipApiError(
                        429,
                        f"Rate limit exceeded; retry after {wait_seconds} seconds",
                        code=err_code or "RATE_LIMITED",
                        correlation_id=corr_id,
                        idempotency_key=idempotency_key,
                        raw_payload=payload,
                    ) from error

                # 409 - IDEMPOTENCY_IN_PROGRESS (aguardar e tentar novamente com a mesma chave)
                if error.code == 409 and (err_code == "IDEMPOTENCY_IN_PROGRESS" or "in progress" in str(err_msg).lower()):
                    wait_seconds = self._retry_after(error)
                    if attempt < max_attempts:
                        time.sleep(wait_seconds)
                        continue
                    raise ResellershipApiError(
                        409,
                        "The original request is still in progress; retry shortly",
                        code=err_code or "IDEMPOTENCY_IN_PROGRESS",
                        correlation_id=corr_id,
                        idempotency_key=idempotency_key,
                        raw_payload=payload,
                    ) from error

                # 5xx - Erros temporários de servidor
                if 500 <= error.code < 600 and attempt < max_attempts:
                    time.sleep(min(2 ** (attempt - 1), 8))
                    continue

                raise ResellershipApiError(
                    status=error.code,
                    message=str(err_msg),
                    code=str(err_code) if err_code else None,
                    correlation_id=str(corr_id) if corr_id else None,
                    idempotency_key=idempotency_key,
                    raw_payload=payload,
                ) from error

            except (URLError, TimeoutError, socket.timeout) as error:
                if attempt < max_attempts:
                    time.sleep(min(2 ** (attempt - 1), 8))
                    continue
                raise ResellershipApiError(
                    status=None,
                    message="No response received from Resellership (network timeout)",
                    code="NETWORK_ERROR",
                    idempotency_key=idempotency_key,
                ) from error

        raise RuntimeError("Unreachable retry state")

    @staticmethod
    def _error_payload(error: HTTPError) -> Dict[str, Any]:
        try:
            raw = error.read().decode("utf-8")
            payload = json.loads(raw)
            return payload if isinstance(payload, dict) else {"raw": raw}
        except Exception:
            return {}

    @staticmethod
    def _retry_after(error: HTTPError) -> int:
        try:
            return max(1, int(error.headers.get("Retry-After", "2")))
        except (TypeError, ValueError):
            return 2

    @staticmethod
    def new_intended_action_key() -> str:
        """Gera uma chave única de idempotência (UUIDv4)."""
        return str(uuid.uuid4())

    def get_balance(self) -> Dict[str, Any]:
        """
        GET /balance.php
        Retorna saldo, moeda e estatísticas da carteira do revendedor.
        """
        return self._request_json("GET", "balance.php")

    def get_products(
        self,
        page: int = 1,
        limit: int = 100,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        GET /products.php
        Lista os produtos disponíveis fornecidos pelo master seller.
        """
        params: Dict[str, Any] = {"page": page, "limit": min(limit, 100)}
        if category_id is not None:
            params["category_id"] = category_id
        if search:
            params["search"] = search

        query = urlencode(params)
        return self._request_json("GET", f"products.php?{query}")

    def get_product_details(self, product_id: int) -> Dict[str, Any]:
        """
        GET /product-details.php?id=<id>
        Retorna detalhes de um produto e suas opções/variantes.
        """
        query = urlencode({"id": int(product_id)})
        return self._request_json("GET", f"product-details.php?{query}")

    def create_order(
        self,
        product_id: int,
        quantity: int = 1,
        option_id: Optional[int] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        POST /orders.php
        Efetua a compra de códigos/chaves na API.
        """
        if idempotency_key is None:
            idempotency_key = self.new_intended_action_key()

        body: Dict[str, Any] = {
            "productId": int(product_id),
            "quantity": int(quantity),
        }
        if option_id is not None:
            body["optionId"] = int(option_id)

        return self._request_json(
            method="POST",
            path="orders.php",
            body=body,
            idempotency_key=idempotency_key,
            is_write=True,
        )

    def get_orders(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """
        GET /orders.php
        Retorna lista paginada dos pedidos realizados.
        """
        params = {"page": page, "limit": min(limit, 100)}
        query = urlencode(params)
        return self._request_json("GET", f"orders.php?{query}")

    def get_order(self, order_id: int) -> Dict[str, Any]:
        """
        GET /order.php?id=<id>
        Retorna dados de um pedido específico e seus códigos entregues.
        """
        query = urlencode({"id": int(order_id)})
        return self._request_json("GET", f"order.php?{query}")

    @staticmethod
    def extract_delivered_codes(order_response: Dict[str, Any]) -> List[str]:
        """
        Extrai de forma resiliente a lista de chaves/códigos entregues pela API.
        Suporta respostas onde os dados estão na raiz ou encapsulados em 'data' ou 'order'.
        """
        codes: List[str] = []
        if not isinstance(order_response, dict):
            return codes

        data = order_response.get("data") if isinstance(order_response.get("data"), dict) else {}
        order = order_response.get("order") if isinstance(order_response.get("order"), dict) else {}
        data_order = data.get("order") if isinstance(data.get("order"), dict) else {}

        raw_candidates = [
            order_response.get("codes"),
            data.get("codes"),
            order.get("codes"),
            data_order.get("codes"),
            order_response.get("deliveredCodes"),
            data.get("deliveredCodes"),
            order.get("deliveredCodes"),
            data_order.get("deliveredCodes"),
            order_response.get("delivered_codes"),
            data.get("delivered_codes"),
            order.get("delivered_codes"),
            data_order.get("delivered_codes"),
            order_response.get("deliveredCode"),
            data.get("deliveredCode"),
            order_response.get("code"),
            data.get("code"),
            order.get("code"),
            data_order.get("code"),
        ]

        for cand in raw_candidates:
            if cand is None:
                continue

            # Se vier como dicionário com chaves numéricas ("0", "1", ...) típico de PHP
            if isinstance(cand, dict) and not any(k in cand for k in ("code", "key", "license", "value", "key_string", "code_string")):
                cand = list(cand.values())

            if isinstance(cand, list):
                for item in cand:
                    if isinstance(item, str) and item.strip():
                        codes.append(item.strip())
                    elif isinstance(item, dict):
                        val = (
                            item.get("code")
                            or item.get("key")
                            or item.get("license")
                            or item.get("code_string")
                            or item.get("key_string")
                            or item.get("value")
                        )
                        if val and str(val).strip():
                            codes.append(str(val).strip())
                if codes:
                    break

            elif isinstance(cand, str) and cand.strip():
                codes.append(cand.strip())
                break

            elif isinstance(cand, dict):
                val = (
                    cand.get("code")
                    or cand.get("key")
                    or cand.get("license")
                    or cand.get("code_string")
                    or cand.get("key_string")
                    or cand.get("value")
                )
                if val and str(val).strip():
                    codes.append(str(val).strip())
                    break

        return codes

    @staticmethod
    def extract_order_id(order_response: Dict[str, Any]) -> Optional[Any]:
        """
        Extrai o ID do pedido retornado pela Resellership.
        """
        if not isinstance(order_response, dict):
            return None

        data = order_response.get("data") if isinstance(order_response.get("data"), dict) else {}
        order = order_response.get("order") if isinstance(order_response.get("order"), dict) else {}
        data_order = data.get("order") if isinstance(data.get("order"), dict) else {}

        return (
            order.get("id")
            or data_order.get("id")
            or order.get("orderNumber")
            or data_order.get("orderNumber")
            or data.get("id")
            or data.get("orderId")
            or order_response.get("id")
            or order_response.get("correlationId")
        )
