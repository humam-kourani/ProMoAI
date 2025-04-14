from typing import Any, Callable, List, TypeVar

from promoai.general_utils import constants
from promoai.general_utils.ai_providers import AIProviders
from promoai.prompting.prompt_engineering import ERROR_MESSAGE_FOR_MODEL_GENERATION

T = TypeVar("T")


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
        if ai_provider == AIProviders.GOOGLE.value:
            response = generate_response_with_history_google(
                conversation, api_key, llm_name
            )
        elif ai_provider == AIProviders.ANTHROPIC.value:
            response = generate_response_with_history_anthropic(
                conversation, api_key, llm_name
            )
        else:
            use_responses_api = False
            if ai_provider == AIProviders.DEEPINFRA.value:
                api_url = "https://api.deepinfra.com/v1/openai"
            elif ai_provider == AIProviders.OPENAI.value:
                api_url = "https://api.openai.com/v1"
                use_responses_api = True
            elif ai_provider == AIProviders.DEEPSEEK.value:
                api_url = "https://api.deepseek.com/"
            elif ai_provider == AIProviders.MISTRAL_AI.value:
                api_url = "https://api.mistral.ai/v1/"
            else:
                raise Exception(f"AI provider {ai_provider} is not supported!")
            response = generate_response_with_history(
                conversation,
                api_key,
                llm_name,
                api_url,
                use_responses_api=use_responses_api,
            )
        # print_conversation(conversation)
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


def generate_response_with_history(
    conversation_history, api_key, llm_name, api_url, use_responses_api=False
) -> str:
    """
    Generates a response from the LLM using the conversation history.

    :param conversation_history: The conversation history to be included
    :param api_key: API key
    :param llm_name: model to be used
    :param api_url: API URL to be used
    :param use_responses_api: set True for OpenAI models only
    :return: The content of the LLM response
    """
    import requests

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    messages_payload = []
    for message in conversation_history:
        role = message["role"]
        text = message["content"]
        if use_responses_api:
            processed_message = {
                "role": role,
                "content": [{"type": "input_text", "text": text}],
            }
        else:
            processed_message = {"role": role, "content": text}

        messages_payload.append(processed_message)

    payload = {"model": llm_name}
    if use_responses_api:
        payload["input"] = messages_payload
    else:
        payload["messages"] = messages_payload

    if api_url.endswith("/"):
        api_url = api_url[:-1]

    if use_responses_api:
        response = requests.post(
            api_url + "/responses", headers=headers, json=payload
        ).json()
    else:
        response = requests.post(
            api_url + "/chat/completions", headers=headers, json=payload
        ).json()

    if "error" in response and response["error"]:
        raise Exception(
            "Connection failed! This is the error message: "
            + response["error"]["message"]
        )

    try:
        if use_responses_api:
            return response["output"][-1]["content"][0]["text"]
        else:
            return response["choices"][0]["message"]["content"]
    except Exception:
        raise Exception("Connection failed! This is the response: " + str(response))


def generate_response_with_history_google(
    conversation_history, api_key, google_model
) -> str:
    """
    Generates a response from the LLM using the conversation history.

    :param conversation_history: The conversation history to be included
    :param api_key: Google API key
    :param google_model: Google model to be used
    :return: The content of the LLM response
    """
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(google_model)
    response = model.generate_content(str(conversation_history))
    try:
        return response.text
    except Exception:
        raise Exception("Connection failed! This is the response: " + str(response))


def generate_response_with_history_anthropic(conversation, api_key, llm_name):
    import anthropic

    client = anthropic.Anthropic(
        api_key=api_key,
    )
    message = client.messages.create(
        model=llm_name, max_tokens=8192, messages=conversation
    )
    try:
        return message.content[0].text
    except Exception:
        raise Exception("Connection failed! This is the response: " + str(message))
