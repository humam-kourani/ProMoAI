from pm4py.objects.powl.obj import (
    OperatorPOWL,
    SilentTransition,
    StrictPartialOrder,
    Transition,
)
from pm4py.objects.process_tree.obj import Operator

from promoai.prompting.prompt_engineering import import_statement


def translate_powl_to_code(powl_obj):
    """
    Translates a POWL object from pm4py into code using ModelGenerator.

    Args:
        powl_obj: The POWL object to translate.

    Returns:
        A string containing the Python code that constructs the equivalent POWL model using ModelGenerator.
    """
    code_lines = [import_statement, "gen = ModelGenerator()"]

    var_counter = [0]

    def get_new_var_name():
        var_name = f"var_{var_counter[0]}"
        var_counter[0] += 1
        return var_name

    def process_powl(powl):
        if isinstance(powl, Transition):
            var_name = get_new_var_name()
            if isinstance(powl, SilentTransition):
                code_lines.append(f"{var_name} = None")
            else:
                label = powl.label
                code_lines.append(f"{var_name} = gen.activity('{label}')")
            return var_name

        elif isinstance(powl, OperatorPOWL):
            operator = powl.operator
            children = powl.children
            child_vars = [process_powl(child) for child in children]
            var_name = get_new_var_name()
            if operator == Operator.XOR:
                child_vars_str = ", ".join(child_vars)
                code_lines.append(f"{var_name} = gen.xor({child_vars_str})")
            elif operator == Operator.LOOP:
                if len(child_vars) != 2:
                    raise Exception(
                        "A loop of invalid size! This should not be possible!"
                    )
                do_var = child_vars[0]
                redo_var = child_vars[1]
                code_lines.append(
                    f"{var_name} = gen.loop(do={do_var}, redo={redo_var})"
                )
            else:
                raise Exception("Unknown operator! This should not be possible!")
            return var_name

        elif isinstance(powl, StrictPartialOrder):
            nodes = powl.get_children()
            order = powl.order.get_transitive_reduction()
            node_var_map = {node: process_powl(node) for node in nodes}
            dependencies = []
            nodes_in_edges = set()
            for source in nodes:
                for target in nodes:
                    source_var = node_var_map[source]
                    target_var = node_var_map[target]
                    if order.is_edge(source, target):
                        dependencies.append(f"({source_var}, {target_var})")
                        nodes_in_edges.update([source, target])

            # Include nodes not in any edge as singleton tuples
            for node in nodes:
                if node not in nodes_in_edges:
                    var = node_var_map[node]
                    dependencies.append(f"({var},)")

            dep_str = ", ".join(dependencies)
            var_name = get_new_var_name()
            code_lines.append(
                f"{var_name} = gen.partial_order(dependencies=[{dep_str}])"
            )
            return var_name

        else:
            raise Exception("Unknown POWL object! This should not be possible!")

    final_var = process_powl(powl_obj)
    code_lines.append(f"final_model = {final_var}")

    return "\n".join(code_lines)
