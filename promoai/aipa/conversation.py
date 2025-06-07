from aipa.abstraction import get_simplified_xml_abstraction
from aipa.prompting import add_prompt_strategies
from aipa import constants
from aipa import common


def create_conversation(role, parameters=None):
    if parameters is None:
        parameters = {}

    prompt = add_prompt_strategies(parameters=parameters)
    conversation = [create_message(prompt, role=role, parameters=parameters)]
    return conversation


def create_message(message: str, role, additional_content=None, additional_content_type: str = "text",
                   parameters=None):
    if parameters is None:
        parameters = {}

    model_abstraction = parameters.get("model_abstraction", constants.MODEL_ABSTRACTION)

    if model_abstraction not in ["svg"]:
        content = message
    else:
        content = [{"type": "text", "text": f'{message}'}]
        if additional_content is not None:
            content.append({"type": additional_content_type, additional_content_type: additional_content})

    message = {"role": role, "content": content}

    return message


# def create_process_model_representation(data, role, parameters=None):
#     if parameters is None:
#         parameters = {}

#     model_abstraction = parameters.get("model_abstraction", constants.MODEL_ABSTRACTION)

#     abstraction_message = ""

#     if model_abstraction == "json":
#         textual_representation = data.get('textualRepresentation', '')
#         textual_representation_selected = data.get('textualRepresentationSelected', '')
#         message = f'This is a JSON representing the full BPMN model: {textual_representation}'
#         if textual_representation_selected:

#             message = message + f'\n \n The user has selected the following elements of the BPMN model: {textual_representation_selected}'

#         abstraction_message = create_message(message, role=role, parameters=parameters)
#     elif model_abstraction == "xml":
#         model_xml_string = data.get('modelXmlString', '')

#         reduce_xml_size = parameters.get("reduce_xml_size", constants.REDUCE_XML_SIZE)

#         if reduce_xml_size:
#             model_xml_string = common.reduce_xml_size_using_pm4py(model_xml_string)

#         abstraction_message = create_message(
#             f"This is a text containing the BPMN 2.0 XML of the process: {model_xml_string}", role=role,
#             parameters=parameters)
#     elif model_abstraction == "svg":
#         abstraction_message = create_message("The following messages attach the BPMN 2.0 visual of the process",
#                                              role=role, parameters=parameters)
#     elif model_abstraction == "simplified_xml":
#         model_xml_string = data.get('modelXmlString', '')
#         simplified_xml_string = get_simplified_xml_abstraction(model_xml_string)
#         message = f"This is an XML-like textual representation of the BPMN: {simplified_xml_string}"

#         textual_representation_selected = data.get('textualRepresentationSelected', '')
#         if textual_representation_selected:
#             message = message + f'\n \n The user has selected the following elements of the BPMN model (represented as a json): {textual_representation_selected}'
#         abstraction_message = create_message(message, role=role, parameters=parameters)
#     return abstraction_message

# FILE: conversation.py
# (Assuming other functions like create_conversation are in here too)

# --- Assumed helper functions (based on your code) ---
# def create_message(text, role, parameters=None):
#     """
#     Creates a message dictionary for the conversation.
#     (This is an assumed implementation).
#     """
#     # Parameters might be used for other logic not shown
#     return {"role": role, "content": text}

# def create_conversation(role, parameters):
#     """
#     Placeholder for your conversation creation logic.
#     """
#     # This function's usage in your original code seems to be overwritten,
#     # so its implementation is not critical for this refactoring.
#     pass
# # ----------------------------------------------------


def create_process_model_representation(role: str, model_content: str, parameters: dict, selected_elements_json: str = None) -> dict:
    """
    Creates a standardized message representing a process model in a specified format.

    This function is DECOUPLED: it expects the final model content to be passed
    directly and does not perform any transformations itself (like simplification or reduction).

    Args:
        role (str): The role for the message (e.g., 'user', 'system').
        model_content (str): The pre-formatted model data (e.g., a simplified XML string, a full XML string, or a JSON string).
        parameters (dict): A dictionary of configuration parameters.
                           Expected key: "model_abstraction".
        selected_elements_json (str, optional): A JSON string of selected elements. Defaults to None.

    Returns:
        dict: A message object (e.g., {"role": "system", "content": "..."}).
    """
    model_abstraction = parameters.get("model_abstraction", "simplified_xml") # Defaulting to simplified_xml

    message_text = ""
    if model_abstraction == "json":
        message_text = f'This is a JSON representing the full BPMN model: {model_content}'
        if selected_elements_json:
            message_text += f'\n\n The user has selected the following elements of the BPMN model: {selected_elements_json}'

    elif model_abstraction in ["xml", "simplified_xml"]:
        # This branch now handles both full and simplified XML. The calling code
        # is responsible for providing the correct `model_content`.
        if model_abstraction == "xml":
            message_text = f"This is a text containing the BPMN 2.0 XML of the process: {model_content}"
        else: # simplified_xml
            message_text = f"This is an XML-like textual representation of the BPMN: {model_content}"

        if selected_elements_json:
            message_text += f'\n\n The user has selected the following elements of the BPMN model (represented as a json): {selected_elements_json}'

    elif model_abstraction == "svg":
        message_text = "The following messages attach the BPMN 2.0 visual of the process"

    else:
        # Fallback or error for unknown abstraction
        # You might want to raise a ValueError here instead
        return create_message(f"Error: Unknown model abstraction '{model_abstraction}'.", role="system", parameters=parameters)

    return create_message(message_text, role="system", parameters=parameters)