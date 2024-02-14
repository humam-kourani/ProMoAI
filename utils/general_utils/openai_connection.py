from typing import Callable, List, TypeVar, Any
import requests

T = TypeVar('T')


def generate_result_with_error_handling(conversation: List[dict[str:str]],
                                        extraction_function: Callable[[str, Any], T],
                                        api_key: str,
                                        openai_model: str,
                                        max_iterations=5) \
        -> tuple[T, List[dict[str:str]]]:
    error_history = []
    for iteration in range(max_iterations):
        response = generate_response_with_history(conversation, api_key, openai_model)

        try:
            conversation.append({"role": "system", "content": response})
            print(response)
            result = extraction_function(response, iteration)
            return result, conversation  # Break loop if execution is successful
        except Exception as e:
            error_description = str(e)
            error_history.append(error_description)
            print("Error detected in iteration " + str(iteration + 1))
            new_message = f"Executing your code led to an error! Please update the model to fix the error. Make sure" \
                          f" to save the updated final model is the variable 'final_model'. This is the error" \
                          f" message: {error_description}"
            print(new_message)
            conversation.append({"role": "user", "content": new_message})

    raise Exception(openai_model + " failed to fix the errors after " + str(max_iterations) +
                    " iterations! This is the error history: " + str(error_history))


def generate_response_with_history(conversation_history, api_key, openai_model) -> str:
    """
    Generates a response from the LLM using the conversation history.

    :param conversation_history: The conversation history to be included
    :param api_key: OpenAI API key
    :param openai_model: OpenAI model to be used
    :return: The content of the LLM response
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    messages_payload = []
    for message in conversation_history:
        messages_payload.append({
            "role": message["role"],
            "content": [
                {
                    "type": "text",
                    "text": message["content"]
                }
            ]
        })

    payload = {
        "model": openai_model,
        "messages": messages_payload,
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload).json()

    try:
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        raise Exception("Connection to OpenAI failed! This is the response: " + str(response))
