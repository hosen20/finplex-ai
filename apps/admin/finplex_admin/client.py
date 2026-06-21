from typing import Any

import httpx


class AdminApiError(RuntimeError):
    """Raised when the Finplex API returns an unsuccessful response."""


class FinplexAdminClient:
    """Small HTTP client used by the Streamlit Platform Admin app."""

    def __init__(self, *, base_url: str, access_token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token

    def login(self, *, email: str, password: str) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        return self._parse_response(response)

    def me(self) -> dict[str, Any]:
        response = httpx.get(
            f"{self.base_url}/auth/me",
            headers=self._headers(),
            timeout=10,
        )
        return self._parse_response(response)

    def health(self) -> dict[str, Any]:
        response = httpx.get(f"{self.base_url}/health", timeout=10)
        return self._parse_response(response)

    def readiness(self) -> dict[str, Any]:
        response = httpx.get(f"{self.base_url}/health/ready", timeout=10)
        return self._parse_response(response)

    def list_tenants(self) -> list[dict[str, Any]]:
        response = httpx.get(
            f"{self.base_url}/tenants",
            headers=self._headers(),
            timeout=10,
        )
        return self._parse_response(response)

    def create_tenant(
        self,
        *,
        name: str,
        erp_provider: str,
        crm_provider: str,
    ) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/tenants",
            headers=self._headers(),
            json={
                "name": name,
                "erp_provider": erp_provider,
                "crm_provider": crm_provider,
            },
            timeout=10,
        )
        return self._parse_response(response)

    def set_tenant_status(
        self,
        *,
        tenant_id: str,
        status: str,
    ) -> dict[str, Any]:
        endpoint = "reactivate" if status == "active" else "suspend"
        response = httpx.post(
            f"{self.base_url}/tenants/{tenant_id}/{endpoint}",
            headers=self._headers(),
            timeout=10,
        )
        return self._parse_response(response)

    def list_users(self, *, tenant_id: str) -> list[dict[str, Any]]:
        response = httpx.get(
            f"{self.base_url}/users",
            headers=self._headers(),
            params={"tenant_id": tenant_id},
            timeout=10,
        )
        return self._parse_response(response)

    def create_user(
        self,
        *,
        tenant_id: str,
        email: str,
        full_name: str,
        password: str,
        role: str,
    ) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/users",
            headers=self._headers(),
            json={
                "tenant_id": tenant_id,
                "email": email,
                "full_name": full_name,
                "password": password,
                "role": role,
            },
            timeout=10,
        )
        return self._parse_response(response)

    def _headers(self) -> dict[str, str]:
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}

    @staticmethod
    def _parse_response(response: httpx.Response) -> Any:
        try:
            data = response.json()
        except ValueError as exc:
            raise AdminApiError(response.text) from exc

        if response.is_error:
            detail = data.get("detail", data) if isinstance(data, dict) else data
            raise AdminApiError(str(detail))

        return data
