from __future__ import annotations

from typing import Callable, List, TypeVar, Any, Optional, Tuple
import logging
import json
import re
import time

import requests
import google.generativeai as genai  # per colleague change
import cohere  # per colleague change

from promoai.general_utils.ai_providers import AIProviders
from promoai.prompting.prompt_engineering import ERROR_MESSAGE_FOR_MODEL_GENERATION
from promoai.general_utils import constants

T = TypeVar("T")

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
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
    re.compile(r"sk-[A-Za-z0-9]{10,}"),                 # OpenAI-style keys
    re.compile(r"ya29\.[A-Za-z0-9\-\._]{20,}"),         # Google access tokens
]

def _redact(s: str, replacement: str = "******") -> str:
    if not s:
        return s
    redacted = s
    for pat in _SECRET_PATTERNS:
        redacted = pat.sub(replacement, redacted)
    redacted = re.sub(r"Bearer\s+[A-Za-z0-9\-\._]{8,}", "Bearer ******", redacted, flags=re.I)
    return redacted


def _user_message(kind: str, extra: Optional[str] = None) -> str:
    base = {
        "bad_request": "The request failed. Check the model name and availability.",
        "auth": "Authentication failed. Please check your API credentials.",
        "rate_limit": "The service is busy right now. Please try again in a moment.",
        "unavailable": "The model service is temporarily unavailable. Please try again.",
        "timeout": "The request took too long and timed out. Please try again.",
        "unexpected": "Something went wrong while generating the answer. Check the model name and availability.",
        "unsupported": "This AI provider isn't supported.",
        "provider_mismatch": "There's a mismatch between the provider and the request.",
    }.get(kind, "Something went wrong.")
    if extra:
        return f"{base} {extra}".strip()
    return base


def _raise_for_status(resp: requests.Response) -> None:
    """Map HTTP errors to our typed exceptions with user-safe messages."""
    status = resp.status_code
    try:
        payload = resp.json()
    except Exception:
        payload = {}

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

    raise UnexpectedResponseError(_user_message("unexpected"), retryable=True)


def _requests_post(url: str, *, headers: dict, json_: dict, timeout_s: Tuple[float, float]) -> dict:
    try:
        resp = requests.post(url, headers=headers, json=json_, timeout=timeout_s)
    except requests.Timeout:
        raise TimeoutError(_user_message("timeout"), retryable=True)
    except requests.RequestException as e:
        logger.warning("Network error to %s: %s", url, _redact(str(e)))
        raise ServiceUnavailableError(_user_message("unavailable"), retryable=True)

    if not (200 <= resp.status_code < 300):
        _raise_for_status(resp)

    try:
        return resp.json()
    except ValueError:
        raise UnexpectedResponseError(_user_message("unexpected"), retryable=True)


# -----------------------------------------------------------------------------
# Public API (keeps colleague’s provider list; keeps robust handling)
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
    elif ai_provider == AIProviders.COHERE.value:
        return generate_response_with_history_cohere(conversation, api_key, llm_name)
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
        elif ai_provider == AIProviders.OPENROUTER.value:
            api_url = "https://openrouter.ai/api/v1"
        elif ai_provider == AIProviders.GROK.value:
            api_url = "https://api.x.ai/v1"
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
    conversation: List[dict[str:str]],
    extraction_function: Callable[[str, Any], T],
    api_key: str,
    llm_name: str,
    ai_provider: str,
    max_iterations=5,
    additional_iterations=5,
    standard_error_message=ERROR_MESSAGE_FOR_MODEL_GENERATION,
) -> tuple[str, any, list[Any]]:
    error_history = []
    for iteration in range(max_iterations + additional_iterations):
        response = query_llm(conversation, api_key, llm_name, ai_provider)
        try:
            conversation.append({"role": "assistant", "content": response})
            auto_duplicate = iteration >= max_iterations
            code, result = extraction_function(response, auto_duplicate)
            return code, result, conversation  # Break loop if execution is successful
        except Exception as e:
            error_description = str(e)
            error_history.append(error_description)
            if constants.ENABLE_PRINTS:
                print("Error detected in iteration " + str(iteration + 1))
            new_message = (
                f"Executing your code led to an error! "
                + standard_error_message
                + "This is the error"
                f" message: {error_description}"
            )
            conversation.append({"role": "user", "content": new_message})

    raise Exception(
        llm_name
        + " failed to fix the errors after "
        + str(max_iterations + 5)
        + " iterations! This is the error history: "
        + str(error_history)
    )


def print_conversation(conversation):
    if constants.ENABLE_PRINTS:
        print("\n\n")
        for index, msg in enumerate(conversation):
            print("\t%d: %s" % (index, str(msg).replace("\n", " ").replace("\r", " ")))
        print("\n\n")


# -----------------------------------------------------------------------------
# Generic OpenAI-compatible providers (OpenAI, DeepInfra, Mistral chat, Deepseek, OpenRouter, Grok)
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

    data = _requests_post(url, headers=headers, json_=payload, timeout_s=(3.05, 60))

    if isinstance(data, dict) and data.get("error"):
        logger.warning("Provider returned error object with 200: %s", _redact(str(data.get("error"))))
        raise ServiceUnavailableError(_user_message("unavailable"), retryable=True)

    try:
        if use_responses_api:
            return data["output"][-1]["content"][0]["text"]
        else:
            return data["choices"][0]["message"]["content"]
    except (KeyError, TypeError):
        logger.warning("Unexpected schema from provider: %s", _redact(str(data))[:1000])
        raise UnexpectedResponseError(_user_message("unexpected"), retryable=True)


# -----------------------------------------------------------------------------
# Google (Gemini) – fixed to use contents/parts format + system_instruction
# -----------------------------------------------------------------------------
def _to_gemini_contents_and_system(
    conversation_history: List[dict[str, str]]
) -> Tuple[Optional[str], List[dict]]:
    """
    Convert OpenAI-style messages to Gemini contents format:
    - system messages -> system_instruction (string, joined with \n\n)
    - user messages   -> {'role': 'user',  'parts': [{'text': ...}]}
    - assistant msgs  -> {'role': 'model', 'parts': [{'text': ...}]}
    """
    system_msgs: List[str] = []
    contents: List[dict] = []

    for m in conversation_history:
        role = m.get("role")
        text = m.get("content", "")
        if role == "system":
            if isinstance(text, str) and text.strip():
                system_msgs.append(text.strip())
            continue

        g_role = "model" if role == "assistant" else "user"
        contents.append({"role": g_role, "parts": [{"text": text}]})

    system_instruction = "\n\n".join(system_msgs) if system_msgs else None
    return system_instruction, contents


def generate_response_with_history_google(
    conversation_history: List[dict[str, str]],
    api_key: str,
    google_model: str,
) -> str:
    """
    Generates a response from the Google (Gemini) API using the conversation history.
    Expects OpenAI-style messages in `conversation_history`.
    """
    try:
        genai.configure(api_key=api_key)

        system_instruction, contents = _to_gemini_contents_and_system(conversation_history)

        # Instantiate model with system_instruction if present
        if system_instruction:
            model = genai.GenerativeModel(model_name=google_model, system_instruction=system_instruction)
        else:
            model = genai.GenerativeModel(model_name=google_model)

        response = model.generate_content(contents)

        try:
            return response.text  # type: ignore[attr-defined]
        except Exception:
            # Defensive fallback if .text is missing
            if hasattr(response, "candidates") and response.candidates:
                cand = response.candidates[0]
                parts = getattr(cand, "content", None)
                if parts and getattr(parts, "parts", None):
                    texts = [getattr(p, "text", "") for p in parts.parts if getattr(p, "text", "")]
                    if texts:
                        return "\n".join(texts)
            raise UnexpectedResponseError(_user_message("unexpected"), retryable=True)

    except Exception as e:
        text = str(e)
        lower = text.lower()
        if "api key" in lower or "permission" in lower or "unauthorized" in lower:
            raise AuthError(_user_message("auth"), retryable=False)
        if "rate" in lower or "exceeded" in lower or "quota" in lower:
            raise RateLimitError(_user_message("rate_limit"), retryable=True)
        if "timeout" in lower or "timed out" in lower:
            raise TimeoutError(_user_message("timeout"), retryable=True)
        if "not found" in lower or ("model" in lower and ("not" in lower or "unknown" in lower)):
            raise BadRequestError(_user_message("bad_request"), retryable=False)

        logger.error("Google provider error: %s", _redact(text))
        raise ServiceUnavailableError(_user_message("unavailable"), retryable=True)


# -----------------------------------------------------------------------------
# Anthropic
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Cohere (v2)
# -----------------------------------------------------------------------------
def generate_response_with_history_cohere(
    conversation: List[dict[str, str]],
    api_key: str,
    llm_name: str,
) -> str:
    """
    Generates a response from the Cohere API using the conversation history.
    """
    try:
        client = cohere.ClientV2(api_key)
        # Cohere v2 accepts OpenAI-style message dicts with 'role' and 'content'
        response = client.chat(model=llm_name, messages=conversation)
    except Exception as e:
        text = str(e)
        lower = text.lower()
        if "invalid api key" in lower or "unauthorized" in lower:
            raise AuthError(_user_message("auth"), retryable=False)
        if "rate" in lower or "quota" in lower:
            raise RateLimitError(_user_message("rate_limit"), retryable=True)
        if "timeout" in lower or "timed out" in lower:
            raise TimeoutError(_user_message("timeout"), retryable=True)
        logger.error("Cohere provider error: %s", _redact(text))
        raise ServiceUnavailableError(_user_message("unavailable"), retryable=True)

    try:
        # Typical: response.message.content[0].text
        return response.message.content[0].text  # type: ignore[attr-defined,index]
    except Exception:
        logger.warning("Unexpected schema from Cohere: %s", _redact(str(response))[:1000])
        raise UnexpectedResponseError(_user_message("unexpected"), retryable=True)
