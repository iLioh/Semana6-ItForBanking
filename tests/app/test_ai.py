import httpx
import pytest
from openai import APIStatusError, APITimeoutError, OpenAI
from pydantic import ValidationError

from src.app.ai import AzureOpenAIProvider, ComplaintClassification, KYCResult, MockAIProvider
from src.app.config import AppSettings


def test_ai_schemas_and_fake() -> None:
    with pytest.raises(ValidationError):
        ComplaintClassification.model_validate({"category": "CONSULTA"})
    with pytest.raises(ValidationError):
        KYCResult.model_validate({"status": "APROBADO"})
    provider = MockAIProvider()
    context = {"text": "No reconozco una compra con mi tarjeta"}
    assert provider.generate("prompt", ComplaintClassification, context) == provider.generate(
        "prompt", ComplaintClassification, context
    )


@pytest.mark.parametrize("status_code", [429, 503])
def test_azure_provider_bounded_retries_with_fake_transport(status_code: int) -> None:
    attempts = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(request)
        return httpx.Response(status_code, json={"error": {"message": "fake failure"}})

    provider = AzureOpenAIProvider(AppSettings(
        ai_provider="azure", azure_openai_endpoint="https://invalid.local",
        azure_openai_api_key="fake", azure_openai_deployment="fake",
    ))
    provider.client = OpenAI(api_key="fake", base_url="https://invalid.local/openai/v1/",
                             max_retries=2, http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(APIStatusError):
        provider.generate("{{text}}", ComplaintClassification, {"text": "queja simulada"})
    assert len(attempts) == 3


def test_azure_provider_timeout_has_bounded_retries() -> None:
    attempts = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(request)
        raise httpx.ReadTimeout("fake timeout", request=request)

    provider = AzureOpenAIProvider(AppSettings(
        ai_provider="azure", azure_openai_endpoint="https://invalid.local",
        azure_openai_api_key="fake", azure_openai_deployment="fake",
    ))
    provider.client = OpenAI(api_key="fake", base_url="https://invalid.local/openai/v1/",
                             max_retries=2, http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(APITimeoutError):
        provider.generate("{{text}}", ComplaintClassification, {"text": "queja simulada"})
    assert len(attempts) == 3
