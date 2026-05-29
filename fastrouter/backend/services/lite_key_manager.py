"""Manages LiteLLM virtual keys for proxy authentication and access control.

Each customer provider key gets a corresponding LiteLLM virtual key.
The virtual key handles proxy auth, model access control, and rate limiting.
Customer's provider API key is injected at request time via the api_key
field in the chat completion body — not via stored litellm_params.
"""

import httpx

from backend.config import get_settings

settings = get_settings()


class LiteKeyManager:
    """Creates and deletes LiteLLM virtual keys via the admin API."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _admin_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {settings.litellm_master_key}",
            "Content-Type": "application/json",
        }

    async def create_key(
        self,
        user_id: str,
        provider_key_id: str,
        provider: str,
        api_key: str,
        models: list[str] | None = None,
    ) -> str | None:
        """Create a LiteLLM virtual key for proxy auth and access control.

        Returns the virtual key string, or None if LiteLLM is unreachable.
        The customer's provider API key is NOT stored in the virtual key —
        it is injected at request time via the api_key field in the chat body.
        """
        if models is None:
            models = []

        payload: dict = {
            "key_alias": provider,
            "models": models,
            "metadata": {
                "user_id": user_id,
                "fastrouter_pk_id": provider_key_id,
                "provider": provider,
            },
        }

        try:
            response = await self.client.post(
                f"{settings.litellm_url}/key/generate",
                json=payload,
                headers=self._admin_headers(),
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("key")
            return None
        except httpx.ConnectError:
            return None

    async def update_key_models(self, lite_key: str, models: list[str]) -> bool:
        """Update the models list on an existing LiteLLM virtual key."""
        try:
            response = await self.client.post(
                f"{settings.litellm_url}/key/update",
                json={"key": lite_key, "models": models},
                headers=self._admin_headers(),
            )
            return response.status_code == 200
        except httpx.ConnectError:
            return False

    async def delete_key(self, lite_key: str) -> bool:
        """Delete a LiteLLM virtual key. Returns True on success."""
        try:
            response = await self.client.post(
                f"{settings.litellm_url}/key/delete",
                json={"keys": [lite_key]},
                headers=self._admin_headers(),
            )
            return response.status_code == 200
        except httpx.ConnectError:
            return False


_key_manager: LiteKeyManager | None = None


def get_key_manager() -> LiteKeyManager:
    global _key_manager
    if _key_manager is None:
        _key_manager = LiteKeyManager()
    return _key_manager
