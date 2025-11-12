import re
import traceback


def extract_final_python_code(response_text):
    python_code_pattern = r"```python(.*?)```"
    allowed_import_path = "promoai.model_generation.generator"
    allowed_import_class = "ModelGenerator"
    any_import_pattern = r"^\s*(from\s+\S+\s+import\s+\S+|import\s+\S+)"
    allowed_import_pattern = (
        r"^\s*(from\s+"
        + re.escape(allowed_import_path)
        + r"\s+import\s+"
        + re.escape(allowed_import_class)
        + r"|import\s+"
        + re.escape(allowed_import_path)
        + r"\."
        + re.escape(allowed_import_class)
        + r")\s*$"
    )

    matches = re.findall(python_code_pattern, response_text, re.DOTALL)

    if matches:
        python_snippet = matches[-1].strip()
        lines = python_snippet.split("\n")

        for line in lines:
            if re.match(any_import_pattern, line):
                if not re.match(allowed_import_pattern, line):
                    raise Exception(
                        "Python snippet does not meet the import statement requirements! Only the following import"
                        " statement is allowed: "
                        + "from "
                        + allowed_import_path
                        + " import "
                        + allowed_import_class
                    )
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
                    error_line = code.split("\n")[line_number - 1]
                except IndexError:
                    error_line = "Line number out of range."
                break

        if line_number:
            error_details = f'Error occurred at line {line_number}: "{error_line}" with message: {error_msg}'
        else:
            error_details = (
                f"Error occurred with message: {error_msg}. \n The error occurred with trying to execute "
                f"the following extracted code: {code}. "
            )

        raise Exception(error_details)

def extract_resources_from_code(code):
    activity_pattern = re.compile(r"""
        gen\.activity\(
        \s*\"(?P<activity>[^\"]+)\" 
        
        # Start an optional non-capturing group for the pool and lane arguments.
        (?: 
            ,\s* # Arguments must be preceded by a comma and optional whitespace
            
            # Group the two main patterns together
            (?:
                # Pattern 1: Positional arguments (e.g., Hospital, Nurse)
                (?P<pool_pos>[A-Z_]+)\s*,\s*(?P<lane_pos>[A-Z_]+)
                |
                # Pattern 2: Keyword arguments (e.g., pool="Bank", lane=None)
                pool\s*=\s*(?P<pool_kw>\"[^\"]+\"|None)\s*,\s*
                lane\s*=\s*(?P<lane_kw>\"[^\"]+\"|None)
            )
        )? # The '?' makes the entire pool/lane section optional
        \s*\) # Match the closing parenthesis
    """, re.VERBOSE)

    resources = {}
    
    def _process_kw_arg(value):
        if value is None or value == 'None':
            return None
        return value.strip('"')

    for match in activity_pattern.finditer(code):
        activity = match.group('activity')
        
        if match.group('pool_pos') is not None:
            # Matched positional variables (Pattern 1)
            pool = match.group('pool_pos')
            lane = match.group('lane_pos')
        elif match.group('pool_kw') is not None:
            # Matched keyword arguments (Pattern 2)
            pool = _process_kw_arg(match.group('pool_kw'))
            lane = _process_kw_arg(match.group('lane_kw'))
        else:
            # Only the activity name was provided
            pool, lane = None, None
            
        resources[activity] = (pool, lane)
        
    return resources
