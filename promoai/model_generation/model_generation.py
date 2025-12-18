from typing import Any, List

from powl.objects.obj import POWL

from promoai.general_utils.llm_connection import generate_result_with_error_handling
from promoai.model_generation.code_extraction import (
    execute_code_and_get_variable,
    extract_final_python_code,
)
from promoai.model_generation.validation import (
    validate_partial_orders_with_missing_transitive_edges,
    validate_resource_structure,
)


def extract_model_from_response(
    response: str, auto_duplicate: False
) -> tuple[str, POWL]:
    if auto_duplicate:
        response = response.replace("ModelGenerator()", "ModelGenerator(True, True)")
    extracted_code = extract_final_python_code(response)
    variable_name = "final_model"
    result = execute_code_and_get_variable(extracted_code, variable_name)
    result = result.simplify()
    # validate_unique_transitions(result)
    validate_partial_orders_with_missing_transitive_edges(result)
    validate_resource_structure(result)
    return extracted_code, result


def generate_model(
    conversation: List[dict[str:str]],
    api_key: str,
    llm_name: str,
    ai_provider: str,
    llm_args: dict = None,
    max_iterations=10,
    additional_iterations=5,
) -> tuple[str, POWL, list[Any]]:
    return generate_result_with_error_handling(
        conversation=conversation,
        extraction_function=extract_model_from_response,
        api_key=api_key,
        llm_name=llm_name,
        ai_provider=ai_provider,
        llm_args=llm_args,
        max_iterations=max_iterations,
        additional_iterations=additional_iterations,
    )
