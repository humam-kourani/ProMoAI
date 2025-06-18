from pm4py import PetriNet
from pm4py.objects.powl.BinaryRelation import BinaryRelation
from pm4py.objects.powl.obj import Operator, OperatorPOWL, POWL, StrictPartialOrder

from promoai.pn_to_powl.converter_utils.cut_detection import (
    mine_base_case,
    mine_loop,
    mine_partial_order,
    mine_self_loop,
    mine_xor,
)

from promoai.pn_to_powl.converter_utils.preprocessing import (
    preprocess,
    validate_workflow_net,
)
from promoai.pn_to_powl.converter_utils.subnet_creation import (
    apply_partial_order_projection,
    clone_subnet,
)
from promoai.pn_to_powl.converter_utils.weak_reachability import (
    get_simplified_reachability_graph,
)


def convert_workflow_net_to_powl(net: PetriNet) -> POWL:
    """
    Convert a Petri net to a POWL model.

    Parameters:
    - net: PetriNet

    Returns:
    - POWL model
    """
    start_place, end_place = validate_workflow_net(net)
    net = preprocess(net)
    res = __translate_petri_to_powl(net, start_place, end_place)
    return res


def __translate_petri_to_powl(
    net: PetriNet, start_place: PetriNet.Place, end_place: PetriNet.Place
) -> POWL:

    base_case = mine_base_case(net)
    if base_case:
        return base_case

    reachability_map = get_simplified_reachability_graph(net)

    choice_branches = mine_xor(net, reachability_map)
    if len(choice_branches) > 1:
        return __translate_xor(net, start_place, end_place, choice_branches)

    self_loop = mine_self_loop(net, start_place, end_place)
    if self_loop:
        return __translate_loop(
            net, self_loop[0], self_loop[1], self_loop[2], self_loop[3]
        )

    do, redo = mine_loop(net, start_place, end_place)
    if do and redo:
        return __translate_loop(net, do, redo, start_place, end_place)

    partitions = mine_partial_order(net, end_place, reachability_map)
    if len(partitions) > 1:
        return __translate_partial_order(net, partitions, start_place, end_place)

    raise Exception(
        f"Failed to detected a POWL structure over the following transitions: {net.transitions}"
    )


def __translate_xor(
    net: PetriNet,
    start_place: PetriNet.Place,
    end_place: PetriNet.Place,
    choice_branches: list[set[PetriNet.Transition]],
):
    children = []
    for branch in choice_branches:
        child_powl = __create_sub_powl_model(net, branch, start_place, end_place)
        children.append(child_powl)
    xor_operator = OperatorPOWL(operator=Operator.XOR, children=children)
    return xor_operator


def __translate_loop(
    net: PetriNet,
    do_nodes,
    redo_nodes,
    start_place: PetriNet.Place,
    end_place: PetriNet.Place,
) -> OperatorPOWL:
    do_powl = __create_sub_powl_model(net, do_nodes, start_place, end_place)
    redo_powl = __create_sub_powl_model(net, redo_nodes, end_place, start_place)
    loop_operator = OperatorPOWL(operator=Operator.LOOP, children=[do_powl, redo_powl])
    return loop_operator


def __validate_partial_order(po: StrictPartialOrder):
    po.order.add_transitive_edges()
    if po.order.is_irreflexive():
        return po
    else:
        raise Exception("Conversion failed!")


def __translate_partial_order(
    net, transition_groups, i_place: PetriNet.Place, f_place: PetriNet.Place
):

    groups = [tuple(g) for g in transition_groups]
    transition_to_group_map = {transition: g for g in groups for transition in g}

    group_start_places = {g: set() for g in groups}
    group_end_places = {g: set() for g in groups}
    temp_po = BinaryRelation(groups)

    for p in net.places:
        sources = {arc.source for arc in p.in_arcs}
        targets = {arc.target for arc in p.out_arcs}

        # if p is start place and (p -> t), then p should be a start place in the subnet that contains t
        if p == i_place:
            for t in targets:
                group_start_places[transition_to_group_map[t]].add(p)
        # if p is end place and (t -> p), then p should be end place in the subnet that contains t
        if p == f_place:
            for t in sources:
                group_end_places[transition_to_group_map[t]].add(p)

        # if (t1 -> p -> t2) and t1 and t2 are in different subsets, then add an edge in the partial order
        # and set p as end place in g1 and as start place in g2
        for t1 in sources:
            group_1 = transition_to_group_map[t1]
            for t2 in targets:
                group_2 = transition_to_group_map[t2]
                if group_1 != group_2:
                    temp_po.add_edge(group_1, group_2)
                    group_end_places[group_1].add(p)
                    group_start_places[group_2].add(p)

    group_to_powl_map = {}
    children = []
    for group in groups:

        subnet, subnet_start_place, subnet_end_place = apply_partial_order_projection(
            net, set(group), group_start_places[group], group_end_places[group]
        )
        child = __translate_petri_to_powl(subnet, subnet_start_place, subnet_end_place)

        group_to_powl_map[group] = child
        children.append(child)

    po = StrictPartialOrder(children)
    for source in temp_po.nodes:
        new_source = group_to_powl_map[source]
        for target in temp_po.nodes:
            if temp_po.is_edge(source, target):
                new_target = group_to_powl_map[target]
                po.order.add_edge(new_source, new_target)

    po = __validate_partial_order(po)
    return po


def __create_sub_powl_model(
    net,
    branch: set[PetriNet.Transition],
    start_place: PetriNet.Place,
    end_place: PetriNet.Place,
):
    subnet, subnet_start_place, subnet_end_place = clone_subnet(
        net, branch, start_place, end_place
    )
    powl = __translate_petri_to_powl(subnet, subnet_start_place, subnet_end_place)
    return powl
