import time
from copy import deepcopy

import ftfy

from constants import DISABLE_LLM_CONNECTION
from utils.conversation import create_conversation, create_message, create_process_model_representation
from utils.openai_connection import generate_response_with_history

def chat_with_llm(data, session=None, stream=False):
    """
    Generate a response from the LLM with or without streaming.
    When streaming is enabled, this function yields each chunk from the response.
    """
    if session is None:
        session = {}

    user_message = data.get('message', '')
    parameters = data.get('parameters', {})
    parameters["session_key"] = session.get("session_key", "")

    # Initialize conversation if not already present.
    if 'conversation' not in session:
        session['conversation'] = create_conversation(role="system",
        parameters=parameters)
        session['conversation'].append(
            create_process_model_representation(data, role="system", parameters=parameters)
        )

    # Add the user message to the conversation history.
    message = create_message(user_message, role="user", parameters=parameters)
    session['conversation'].append(message)

    if DISABLE_LLM_CONNECTION:
        new_message = "The connection to the LLM is disabled!"
        session['conversation'].append(
            create_message(new_message, role="system", parameters=parameters)
        )
        return new_message

    if stream:
        # Call generate_response_with_history with stream=True.
        # This will yield Ollama’s actual response chunks.
        for chunk in generate_response_with_history(data, session, stream=True, parameters=parameters):
            # You can add additional formatting (like extra newlines) if needed.
            yield ftfy.fix_text(chunk)
        # Optionally, update the conversation history with the final chunk.
        # (Note: the generate_response_with_history function is expected to update history.)
        return
    else:
        # If not streaming, get the full response at once.
        new_message, updated_history = generate_response_with_history(data, session, stream=False, parameters=parameters)
        session['conversation'] = updated_history
        return new_message
