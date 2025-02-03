import json
import traceback
from typing import Callable, List, TypeVar, Any
from promoai.general_utils.ai_providers import AIProviders
from promoai.prompting.prompt_engineering import ERROR_MESSAGE_FOR_MODEL_GENERATION
from promoai import constants

T = TypeVar('T')


def generate_result_with_error_handling(conversation: List[dict[str:str]],
                                        extraction_function: Callable[[str, Any], T],
                                        api_key: str,
                                        llm_name: str,
                                        ai_provider: str,
                                        max_iterations=5,
                                        additional_iterations=5,
                                        standard_error_message=ERROR_MESSAGE_FOR_MODEL_GENERATION) \
        -> tuple[str, any, list[Any]]:
    error_history = []
    for iteration in range(max_iterations + additional_iterations):
        if ai_provider == AIProviders.GOOGLE.value:
            response = generate_response_with_history_google(conversation, api_key, llm_name)
        elif ai_provider == AIProviders.ANTHROPIC.value:
            response = generate_response_with_history_anthropic(conversation, api_key, llm_name)
        else:
            if ai_provider == AIProviders.DEEPINFRA.value:
                api_url = "https://api.deepinfra.com/v1/openai"
            elif ai_provider == AIProviders.OPENAI.value:
                api_url = "https://api.openai.com/v1"
            elif ai_provider == AIProviders.DEEPSEEK.value:
                api_url = "https://api.deepseek.com/"
            elif ai_provider == AIProviders.MISTRAL_AI.value:
                api_url = "https://api.mistral.ai/v1/"
            else:
                raise Exception(f"AI provider {ai_provider} is not supported!")
            response = generate_response_with_history(conversation, api_key, llm_name, api_url)
        print_conversation(conversation)
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
            new_message = f"Executing your code led to an error! " + standard_error_message + "This is the error" \
                                                                                              f" message: {error_description}"
            conversation.append({"role": "user", "content": new_message})

    raise Exception(llm_name + " failed to fix the errors after " + str(max_iterations + 5) +
                    " iterations! This is the error history: " + str(error_history))


def print_conversation(conversation):
    if constants.ENABLE_PRINTS:
        print("\n\n")
        for index, msg in enumerate(conversation):
            print("\t%d: %s" % (index, str(msg).replace("\n", " ").replace("\r", " ")))
        print("\n\n")


def generate_response_with_history(conversation_history, api_key, llm_name, api_url) -> str:
    """
    Generates a response from the LLM using the conversation history.

    :param conversation_history: The conversation history to be included
    :param api_key: API key
    :param llm_name: model to be used
    :param api_url: API URL to be used
    :return: The content of the LLM response
    """
    import requests

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    messages_payload = []
    for message in conversation_history:
        messages_payload.append({
            "role": message["role"],
            "content": message["content"]
        })

    payload = {
        "model": llm_name,
        "messages": messages_payload
    }

    if api_url.endswith("/"):
        api_url = api_url[:-1]

    complete_url = api_url + "/chat/completions"

    response_message = ""
    streaming_enabled = True

    for m_not_supporting_streaming in ["o1-", "o3-"]:
        if llm_name.lower().startswith(m_not_supporting_streaming):
            streaming_enabled = False

    try:
        if streaming_enabled:
            # some providers for DeepSeek-R1 and distillations might be *very* slow and causing timeout error.
            # this may also happen with other big models (Llama3.1-405B, DeepSeek-V3, ...)
            # streaming solves that :)

            payload["stream"] = True
            chunk_count = 0
            # We add stream=True to requests so we can iterate over chunks
            with requests.post(complete_url, headers=headers, json=payload, stream=True) as resp:
                if resp.status_code != 200:
                    raise Exception(resp.text)

                for line in resp.iter_lines():
                    if not line:
                        continue
                    decoded_line = line.decode("utf-8")

                    # OpenAI-style streaming lines begin with "data: "
                    if decoded_line.startswith("data: "):
                        data_str = decoded_line[len("data: "):].strip()
                        if data_str == "[DONE]":
                            # End of stream
                            break
                        try:
                            data_json = json.loads(data_str)
                            if "choices" in data_json:
                                # Each chunk has a delta with partial content
                                chunk_content = data_json["choices"][0]["delta"].get("content", "")
                                response_message += chunk_content
                                chunk_count += 1
                                # print(chunk_count)
                                if chunk_count % 10 == 0:
                                    # print(chunk_count, len(response_message), response_message.replace("\n", " ").replace("\r", "").strip())
                                    pass
                        except json.JSONDecodeError:
                            # Possibly a keep-alive or incomplete chunk
                            traceback.print_exc()
        else:
            response = requests.post(api_url + "/chat/completions", headers=headers, json=payload)
            if response.status_code != 200:
                raise Exception(response.text)
            response = response.json()
            response_message = response["choices"][0]["message"]["content"]
    except Exception as e:
        raise e
    else:
        return response_message


def generate_response_with_history_google(conversation_history, api_key, google_model) -> str:
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
    except Exception as e:
        raise Exception("Connection failed! This is the response: " + str(response))


def generate_response_with_history_anthropic(conversation, api_key, llm_name):
    import anthropic

    client = anthropic.Anthropic(
        api_key=api_key,
    )
    message = client.messages.create(
        model=llm_name,
        max_tokens=8192,
        messages=conversation
    )
    try:
        return message.content[0].text
    except Exception:
        raise Exception("Connection failed! This is the response: " + str(message))
