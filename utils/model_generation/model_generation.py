from typing import List, Any

from utils.general_utils.llm_connection import generate_result_with_error_handling
from utils.model_generation.code_extraction import extract_final_python_code, execute_code_and_get_variable
from utils.model_generation.validation import validate_partial_orders_with_missing_transitive_edges
from pm4py.objects.powl.obj import POWL


def extract_model_from_response(response: str, auto_duplicate: False) -> tuple[str, POWL]:
    if auto_duplicate:
        response = response.replace('ModelGenerator()', 'ModelGenerator(True, True)')
    extracted_code = extract_final_python_code(response)
    variable_name = 'final_model'
    result = execute_code_and_get_variable(extracted_code, variable_name)
    # validate_unique_transitions(result)
    validate_partial_orders_with_missing_transitive_edges(result)
    return extracted_code, result


def generate_model(conversation: List[dict[str:str]], api_key: str, llm_name: str, ai_provider: str,
                   max_iterations=10, additional_iterations=5) \
        -> tuple[str, POWL, list[Any]]:
    return generate_result_with_error_handling(conversation=conversation,
                                               extraction_function=extract_model_from_response,
                                               api_key=api_key,
                                               llm_name=llm_name,
                                               ai_provider=ai_provider,
                                               max_iterations=max_iterations,
                                               additional_iterations=additional_iterations)
