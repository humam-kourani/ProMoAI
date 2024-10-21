from typing import List

from utils.general_utils.openai_connection import generate_result_with_error_handling
from utils.model_generation.code_extraction import extract_final_python_code, execute_code_and_get_variable
from utils.model_generation.validation import validate_partial_orders_with_missing_transitive_edges
from pm4py.objects.powl.obj import POWL


def extract_model_from_response(response: str, iteration: int) -> POWL:
    if iteration > 3:
        response = response.replace('ModelGenerator()', 'ModelGenerator(True, True)')
    extracted_code = extract_final_python_code(response)
    variable_name = 'final_model'
    result = execute_code_and_get_variable(extracted_code, variable_name)
    # validate_unique_transitions(result)
    validate_partial_orders_with_missing_transitive_edges(result)
    return result


def generate_model(conversation: List[dict[str:str]], api_key: str, openai_model: str, api_url: str) \
        -> tuple[POWL, List[dict[str:str]]]:
    return generate_result_with_error_handling(conversation=conversation,
                                               extraction_function=extract_model_from_response,
                                               api_key=api_key,
                                               openai_model=openai_model,
                                               api_url=api_url,
                                               max_iterations=5)
