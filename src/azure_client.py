"""Cliente de Azure OpenAI utilizado por los ejercicios del laboratorio."""

from __future__ import annotations

from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_fixed

from src.config import AzureOpenAISettings, load_azure_settings


def create_azure_client(
    settings: AzureOpenAISettings | None = None,
) -> tuple[AzureOpenAI, AzureOpenAISettings]:
    """Construye el cliente sin registrar la clave de acceso."""

    resolved_settings = settings or load_azure_settings()
    client = AzureOpenAI(
        api_key=resolved_settings.api_key.get_secret_value(),
        azure_endpoint=str(resolved_settings.endpoint),
        api_version=resolved_settings.api_version,
    )
    return client, resolved_settings


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
def test_azure_connection() -> str:
    """Realiza una solicitud minima para validar endpoint y deployment."""

    client, settings = create_azure_client()
    response = client.chat.completions.create(
        model=settings.deployment,
        messages=[
            {
                "role": "user",
                "content": "Responde unicamente con la palabra OK.",
            }
        ],
        temperature=0,
        max_tokens=5,
    )
    return response.choices[0].message.content or ""
