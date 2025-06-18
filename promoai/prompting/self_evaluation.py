from typing import Dict, List

from promoai.model_generation.code_extraction import (
    execute_code_and_get_variable,
    extract_final_python_code,
)


def extraction_function_dictionary(response: str, keys: List[str]) -> tuple[str, Dict]:
    extracted_code = extract_final_python_code(response)
    print(extracted_code)
    variable_name = "score_dictionary"
    score_dict = execute_code_and_get_variable(extracted_code, variable_name)
    if not isinstance(score_dict, Dict):
        raise Exception(f"Not a dictionary! Found: {score_dict}!")
    if list(score_dict.keys()) == keys:
        return extracted_code, score_dict
    else:
        raise Exception(
            f"Wrong keys in the extracted dictionary! Expected: {keys}; found: {score_dict.keys()}!"
        )


def generate_self_evaluation_prompt(
    description: str, model_codes: Dict[str, str], conformance_evaluation: bool = False
) -> str:
    """
    Generates a prompt for the LLM to evaluate multiple models based on a process description.

    Args:
        description (str): The process description.
        model_codes (Dict[str, str]): A dictionary where keys are model IDs (e.g., 'IT1') and values are
         the corresponding POWL codes.
        conformance_evaluation

    Returns:
        str: The formatted prompt to be sent to the LLM.
    """
    prompt = """You have already generated 4 candidate POWL models for a single process descriptions
     following the previously detailed task. Now, let's forget about the process modeling role and take the role of
     an assistant specialized in evaluating the already generated process models.
     Your task is to assess the quality of the provided POWL models based on how well they capture the behavior
      described in the process description.\n\n"""
    prompt = prompt + f"""This was the process description: {description}\n\n"""
    prompt = (
        prompt
        + f"""The generated POWL models are saved in the following dictionary:: {model_codes}\n\n"""
    )

    if conformance_evaluation:
        prompt += f"""
        **Evaluation Criteria:**
        - **Fitness:** Evaluate how well the process model can reproduce the behaviors of the process according to the
         process description.
        - **Precision:** Evaluate the extent to which the process model exclusively represents behaviors that
         are allowed in the process according to the process description. """
    else:
        prompt += f"""
        **Evaluation Criteria:**
        - **Behavior Accuracy:** How accurately does the model capture the intended process behavior?
        - **Completeness:** Does the model include all necessary activities as described?
        - **Correctness:** Are the control flows (e.g., partial orders, choices, loops) correctly implemented?"""

    prompt += f"""**Output Requirements:**
    - Provide your evaluation scores as a Python dictionary named `score_dictionary`.
    - Use the same keys for your dictionary as the keys in the provided dictionary, i.e., {list(model_codes.keys())}."""

    prompt += """
    - Each value should be a float between 0 and 1, where:
        - **1** indicates the model perfectly captures the described behavior.
        - **0** indicates the model does not capture the described behavior at all.

    **Example Format:**
    ```python
    score_dictionary = {
        'IT1': 0.85,
        'IT2': 0.90,
        'IT3': 0.80,
        'IT4': 0.95
    }
    ```
    Please ensure to include at the end of your response a Python snipped with a dictionary strictly
     following the above Python code format. """

    return prompt
