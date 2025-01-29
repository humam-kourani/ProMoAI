import re
import traceback


def extract_final_python_code(response_text):
    python_code_pattern = r"```python(.*?)```"
    allowed_import_path = "converter_utils.model_generation"
    allowed_import_class = "ModelGenerator"
    any_import_pattern = r"^\s*(from\s+\S+\s+import\s+\S+|import\s+\S+)"
    allowed_import_pattern = r"^\s*(from\s+" + re.escape(allowed_import_path) + r"\s+import\s+" + re.escape(
        allowed_import_class) + r"|import\s+" + re.escape(allowed_import_path) + r"\." + re.escape(
        allowed_import_class) + r")\s*$"

    matches = re.findall(python_code_pattern, response_text, re.DOTALL)

    if matches:
        python_snippet = matches[-1].strip()
        lines = python_snippet.split('\n')

        for line in lines:
            if re.match(any_import_pattern, line):
                if not re.match(allowed_import_pattern, line):
                    raise Exception(
                        "Python snippet does not meet the import statement requirements! Only the following import"
                        " statement is allowed: " + 'from ' + allowed_import_path + ' import ' + allowed_import_class)
        return python_snippet

    else:
        raise Exception("No Python code snippet found!")


def execute_code_and_get_variable(code, variable_name):
    try:
        local_vars = {}
        exec(code, globals(), local_vars)
        try:
            value = local_vars[variable_name]
        except KeyError:
            raise ValueError(f"Variable '{variable_name}' not found!")
        return value
    except Exception:
        exc_type, exc_value, exc_traceback = traceback.sys.exc_info()
        error_msg = traceback.format_exception_only(exc_type, exc_value)[-1].strip()

        line_number, error_line = None, "Error line not directly available."
        filename = "<string>"

        for frame in traceback.extract_tb(exc_traceback):
            if frame.filename == filename:
                line_number = frame.lineno
                try:
                    error_line = code.split('\n')[line_number - 1]
                except IndexError:
                    error_line = "Line number out of range."
                break

        if line_number:
            error_details = f"Error occurred at line {line_number}: \"{error_line}\" with message: {error_msg}"
        else:
            error_details = f"Error occurred with message: {error_msg}. \n The error occurred with trying to execute " \
                            f"the following extracted code: {code}. "

        raise Exception(error_details)
