from utils.powl.obj import POWL, OperatorPOWL, StrictPartialOrder, SilentTransition, Transition
from pm4py.objects.process_tree.obj import Operator as PTOperator
import re


def __indent_powl_string_to_list_str(powl_str):
    max_indent = 1
    powl_str = powl_str.replace('\n', '').replace('\r', '').strip()
    if powl_str.startswith('PO=') or powl_str.startswith('PO('):
        max_indent = 2
    if powl_str.startswith("'"):
        max_indent = 0

    indent_level = 0
    list_strs = []
    formatted_str = ""
    for char in powl_str:
        if char in '({':
            formatted_str += char
            indent_level += 1
            if indent_level <= max_indent:
                list_strs.append(formatted_str)
                formatted_str = '\t' * indent_level
        elif char in ')}':
            indent_level -= 1
            if indent_level < max_indent:
                if formatted_str[-1] not in '({':
                    list_strs.append(formatted_str)
                    formatted_str = '\t' * indent_level
            formatted_str += char
        elif char == ',':
            formatted_str += char
            if indent_level <= max_indent:
                list_strs.append(formatted_str)
                formatted_str = '\t' * indent_level
        else:
            formatted_str += char
    list_strs.append(formatted_str)
    return list_strs


def parse_powl_model_string(powl_string, level=0) -> POWL:
    """
    Parse a POWL model from a string representation of the process model
    (with the same format as the __repr__ and __str__ methods of the POWL model)

    Minimum Viable Example:

        from pm4py.objects.powl.parser import parse_powl_model_string

        powl_model = parse_powl_model_string('PO=(nodes={ NODE1, NODE2, NODE3 }, order={ NODE1-->NODE2 }')
        print(powl_model)


    Parameters
    ------------------
    powl_string
        POWL model expressed as a string (__repr__ of the POWL model)

    Returns
    ------------------
    powl_model
        POWL model
    """
    indented_str_list = __indent_powl_string_to_list_str(powl_string)

    indented_str_list = [x.strip() for x in indented_str_list]
    indented_str_list = [x[:-1] if x and x[-1] == ',' else x for x in indented_str_list]
    PO = POWL()
    nodes = []

    if indented_str_list:
        if indented_str_list[0].startswith('PO=') or indented_str_list[0].startswith('PO('):
            nodes_dict = {}

            # read the nodes of the POWL
            i = 2
            while i < len(indented_str_list):
                if indented_str_list[i] == '}':
                    break
                N = parse_powl_model_string(indented_str_list[i], level + 1)
                nodes_dict[indented_str_list[i]] = N
                nodes.append(N)
                i = i + 1

            pattern = '(' + '|'.join(map(re.escape, list(nodes_dict))) + ')'

            PO = StrictPartialOrder(nodes=nodes)

            # reads the edges of the POWL
            i = i + 2
            while i < len(indented_str_list):
                if indented_str_list[i] == '}':
                    break

                split_list = [x for x in re.split(pattern, indented_str_list[i]) if x]

                if len(split_list) == 3:
                    PO.order.add_edge(nodes_dict[split_list[0]], nodes_dict[split_list[2]])

                i = i + 1

        elif indented_str_list[0].startswith('X'):
            i = 1
            while i < len(indented_str_list):
                if indented_str_list[i] == ')':
                    break
                N = parse_powl_model_string(indented_str_list[i], level + 1)
                nodes.append(N)
                i = i + 1
            PO = OperatorPOWL(PTOperator.XOR, nodes)
        elif indented_str_list[0].startswith('*'):
            i = 1
            while i < len(indented_str_list):
                if indented_str_list[i] == ')':
                    break
                N = parse_powl_model_string(indented_str_list[i], level + 1)
                nodes.append(N)
                i = i + 1
            PO = OperatorPOWL(PTOperator.LOOP, nodes)
        elif indented_str_list[0].startswith('tau'):
            PO = SilentTransition()
        else:
            label = indented_str_list[0]
            if label.startswith("'"):
                label = label[1:-1]
            PO = Transition(label=label)

    return PO
