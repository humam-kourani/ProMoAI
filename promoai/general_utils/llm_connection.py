from __future__ import annotations

from typing import Callable, List, TypeVar, Any, Optional, Tuple
import logging
import json
import os
import re
import time

import requests

from promoai.general_utils.ai_providers import AIProviders
from promoai.prompting.prompt_engineering import ERROR_MESSAGE_FOR_MODEL_GENERATION
from promoai.general_utils import constants

T = TypeVar("T")

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Safe default console handler; app can override
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(_h)
logger.setLevel(logging.INFO)

# -----------------------------------------------------------------------------
# Error model
# -----------------------------------------------------------------------------
class BaseLLMError(Exception):
    """Base class for errors we surface to the frontend (message is user-safe)."""
    user_message: str
    retryable: bool

    def __init__(self, user_message: str, *, retryable: bool = False):
        super().__init__(user_message)
        self.user_message = user_message
        self.retryable = retryable


class BadRequestError(BaseLLMError): ...
class AuthError(BaseLLMError): ...
class RateLimitError(BaseLLMError): ...
class ServiceUnavailableError(BaseLLMError): ...
class TimeoutError(BaseLLMError): ...
class ProviderMismatchError(BaseLLMError): ...
class UnsupportedProviderError(BaseLLMError): ...
class UnexpectedResponseError(BaseLLMError): ...


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{10,}"),   # OpenAI-ish
    re.compile(r"ya29\.[A-Za-z0-9\-_\.]{20,}"),  # Google
]

def _redact(s: str, replacement: str = "******") -> str:
    if not s:
        return s
    redacted = s
    for pat in _SECRET_PATTERNS:
        redacted = pat.sub(replacement, redacted)
    # Also strip long bearer tokens if someone logs headers by accident
    redacted = re.sub(r"Bearer\s+[A-Za-z0-9\-\._]{8,}", "Bearer ******", redacted, flags=re.I)
    return redacted


def _user_message(kind: str, extra: Optional[str] = None) -> str:
    base = {
        "bad_request": "I couldn't understand that request.",
        "auth": "Authentication failed. Please check your API credentials.",
        "rate_limit": "The service is busy right now. Please try again in a moment.",
        "unavailable": "The model service is temporarily unavailable. Please try again.",
        "timeout": "The request took too long and timed out. Please try again.",
        "unexpected": "Something went wrong while generating the answer.",
        "unsupported": "This AI provider isn't supported.",
        "provider_mismatch": "There's a mismatch between the provider and the request.",
    }.get(kind, "Something went wrong.")
    if extra:
        # Append a short, user-friendly tail (no internals)
        return f"{base} {extra}".strip()
    return base


def _raise_for_status(resp: requests.Response) -> None:
    """Map HTTP errors to our typed exceptions with user-safe messages."""
    status = resp.status_code
    try:
        payload = resp.json()
    except Exception:
        payload = {}

    # Avoid leaking provider messages to users; only log them.
    provider_error = payload.get("error") or payload.get("message") or payload
    safe_log = _redact(json.dumps(provider_error, ensure_ascii=False)[:4000])
    logger.debug("Provider HTTP %s response body: %s", status, safe_log)

    if status in (400, 422):
        raise BadRequestError(_user_message("bad_request"), retryable=False)
    if status in (401, 403):
        raise AuthError(_user_message("auth"), retryable=False)
    if status in (429,):
        raise RateLimitError(_user_message("rate_limit"), retryable=True)
    if status in (500, 502, 503, 504):
        raise ServiceUnavailableError(_user_message("unavailable"), retryable=True)

    # Unknown non-2xx
    raise UnexpectedResponseError(_user_message("unexpected"), retryable=True)


def _requests_post(url: str, *, headers: dict, json_: dict, timeout_s: Tuple[float, float]) -> dict:
    try:
        resp = requests.post(url, headers=headers, json=json_, timeout=timeout_s)
    except requests.Timeout:
        # Retryable timeout
        raise TimeoutError(_user_message("timeout"), retryable=True)
    except requests.RequestException as e:
        logger.warning("Network error to %s: %s", url, _redact(str(e)))
        raise ServiceUnavailableError(_user_message("unavailable"), retryable=True)

    if not (200 <= resp.status_code < 300):
        _raise_for_status(resp)

    try:
        return resp.json()
    except ValueError:
        # Successful status but not JSON
        raise UnexpectedResponseError(_user_message("unexpected"), retryable=True)


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------
def query_llm(
    conversation: List[dict[str, str]],
    api_key: str,
    llm_name: str,
    ai_provider: str,
) -> str:
    if ai_provider == AIProviders.GOOGLE.value:
        return generate_response_with_history_google(conversation, api_key, llm_name)
    elif ai_provider == AIProviders.ANTHROPIC.value:
        return generate_response_with_history_anthropic(conversation, api_key, llm_name)
    else:
        use_responses_api_openai = False
        if ai_provider == AIProviders.DEEPINFRA.value:
            api_url = "https://api.deepinfra.com/v1/openai"
        elif ai_provider == AIProviders.OPENAI.value:
            api_url = "https://api.openai.com/v1"
            use_responses_api_openai = True
        elif ai_provider == AIProviders.DEEPSEEK.value:
            api_url = "https://api.deepseek.com"
        elif ai_provider == AIProviders.MISTRAL_AI.value:
            api_url = "https://api.mistral.ai/v1"
        else:
            raise UnsupportedProviderError(_user_message("unsupported"), retryable=False)

        return generate_response_with_history(
            conversation,
            api_key,
            llm_name,
            api_url,
            use_responses_api=use_responses_api_openai,
        )


def generate_result_with_error_handling(
    conversation: List[dict[str, str]],
    extraction_function: Callable[[str, Any], T],
    api_key: str,
    llm_name: str,
    ai_provider: str,
    max_iterations: int = 5,
    additional_iterations: int = 5,
    standard_error_message: str = ERROR_MESSAGE_FOR_MODEL_GENERATION,
) -> Tuple[str, Any, List[Any]]:
    """
    Runs an LLM call then tries to parse/execute with `extraction_function`.
    On failures, feeds the error back into the conversation and retries.
    Only user-safe messages are ever raised to the caller/frontend.
    """
    error_history: list[str] = []
    total_iters = max_iterations + additional_iterations

    for iteration in range(total_iters):
        response = query_llm(conversation, api_key, llm_name, ai_provider)
        try:
            conversation.append({"role": "assistant", "content": response})
            auto_duplicate = iteration >= max_iterations
            code, result = extraction_function(response, auto_duplicate)
            return code, result, conversation
        except BaseLLMError as e:
            # Our typed errors (from provider or parsing)
            error_history.append(e.user_message)
            if constants.ENABLE_PRINTS:
                print(f"Error detected in iteration {iteration + 1}: {e.user_message}")
            # If not retryable, bail early with the user-safe text
            if not e.retryable:
                raise e
            # Retryable: ask the model to self-correct
            new_message = (
                "Executing your code led to an error. "
                f"{standard_error_message} "
                f"This is the error message: {e.user_message}"
            )
            conversation.append({"role": "user", "content": new_message})
        except Exception as e:
            # Unknown/parse-time error: log details, show safe text
            safe = _user_message("unexpected")
            error_history.append(safe)
            logger.exception("Unexpected parsing/extraction error: %s", _redact(str(e)))
            if constants.ENABLE_PRINTS:
                print(f"Error detected in iteration {iteration + 1}: {safe}")
            new_message = (
                "Executing your code led to an error. "
                f"{standard_error_message} "
                f"This is the error message: {safe}"
            )
            conversation.append({"role": "user", "content": new_message})

    # If we got here, retries failed—return a concise, user-safe summary
    fail_msg = (
        f"{llm_name} couldn't fix the errors after {total_iters} attempts. "
        "Please try again later."
    )
    raise ServiceUnavailableError(fail_msg, retryable=True)


def print_conversation(conversation):
    if constants.ENABLE_PRINTS:
        print("\n\n")
        for index, msg in enumerate(conversation):
            print("\t%d: %s" % (index, str(msg).replace("\n", " ").replace("\r", " ")))
        print("\n\n")


# -----------------------------------------------------------------------------
# Provider calls
# -----------------------------------------------------------------------------
def generate_response_with_history(
    conversation_history: List[dict[str, str]],
    api_key: str,
    llm_name: str,
    api_url: str,
    use_responses_api: bool = False,
) -> str:
    """
    Generates a response from the LLM using the conversation history.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    messages_payload = [{"role": m["role"], "content": m["content"]} for m in conversation_history]

    payload = {"model": llm_name}
    if use_responses_api:
        payload["input"] = messages_payload
        endpoint = "/responses"
    else:
        payload["messages"] = messages_payload
        endpoint = "/chat/completions"

    api_url = api_url.rstrip("/")
    url = f"{api_url}{endpoint}"

    # Short connect timeout, reasonable read timeout
    data = _requests_post(url, headers=headers, json_=payload, timeout_s=(3.05, 60))

    # Provider-level error objects sometimes come back with 200; check defensively
    if isinstance(data, dict) and data.get("error"):
        logger.warning("Provider returned error object with 200: %s", _redact(str(data.get("error"))))
        raise ServiceUnavailableError(_user_message("unavailable"), retryable=True)

    try:
        if use_responses_api:
            return data["output"][-1]["content"][0]["text"]
        else:
            return data["choices"][0]["message"]["content"]
    except (KeyError, TypeError) as e:
        logger.warning("Unexpected schema from provider: %s", _redact(str(data))[:1000])
        raise UnexpectedResponseError(_user_message("unexpected"), retryable=True)


def generate_response_with_history_google(
    conversation_history: List[dict[str, str]],
    api_key: str,
    google_model: str,
) -> str:
    """
    Generates a response from the LLM using the conversation history.
    """
    try:
        import google.generativeai as genai
    except Exception:
        raise ProviderMismatchError(_user_message("provider_mismatch"), retryable=False)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(google_model)
        # Keep the input small + structured; avoid dumping internals in errors
        response = model.generate_content(conversation_history)
        return response.text  # type: ignore[attr-defined]
    except genai.types.generation_types.StopCandidateException as e:  # type: ignore[attr-defined]
        logger.info("Google stop condition: %s", _redact(str(e)))
        raise ServiceUnavailableError(_user_message("unavailable"), retryable=True)
    except genai.types.generation_types.BlockedPromptException as e:  # type: ignore[attr-defined]
        logger.info("Google safety block: %s", _redact(str(e)))
        raise BadRequestError(_user_message("bad_request"), retryable=False)
    except Exception as e:
        text = str(e)
        if "API key" in text or "permission" in text.lower():
            raise AuthError(_user_message("auth"), retryable=False)
        if "rate" in text.lower():
            raise RateLimitError(_user_message("rate_limit"), retryable=True)
        if "timeout" in text.lower():
            raise TimeoutError(_user_message("timeout"), retryable=True)
        logger.exception("Google provider error: %s", _redact(text))
        raise ServiceUnavailableError(_user_message("unavailable"), retryable=True)


def generate_response_with_history_anthropic(
    conversation: List[dict[str, str]],
    api_key: str,
    llm_name: str,
) -> str:
    try:
        import anthropic
    except Exception:
        raise ProviderMismatchError(_user_message("provider_mismatch"), retryable=False)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=llm_name,
            max_tokens=8192,
            messages=conversation,
        )
        return message.content[0].text  # type: ignore[index]
    except anthropic.RateLimitError:
        raise RateLimitError(_user_message("rate_limit"), retryable=True)
    except anthropic.AuthenticationError:
        raise AuthError(_user_message("auth"), retryable=False)
    except anthropic.APIStatusError as e:
        logger.warning("Anthropic APIStatusError: %s", _redact(str(e)))
        raise ServiceUnavailableError(_user_message("unavailable"), retryable=True)
    except Exception as e:
        text = str(e)
        if "timeout" in text.lower():
            raise TimeoutError(_user_message("timeout"), retryable=True)
        logger.exception("Anthropic provider error: %s", _redact(text))
        raise ServiceUnavailableError(_user_message("unavailable"), retryable=True)
