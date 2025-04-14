from copy import copy
from itertools import combinations

from pm4py.objects.petri_net.obj import PetriNet
from pm4py.objects.petri_net.utils import petri_utils as pn_util

from promoai.pn_to_powl.converter_utils.subnet_creation import (
    add_arc_from_to,
    clone_place,
    pn_transition_to_powl,
)
from promoai.pn_to_powl.converter_utils.weak_reachability import (
    get_reachable_transitions_from_place_to_another,
)


def mine_base_case(net: PetriNet):
    if len(net.transitions) == 1 and len(net.places) == 2 == len(net.arcs):
        activity = list(net.transitions)[0]
        powl_transition = pn_transition_to_powl(activity)
        return powl_transition
    return None


def mine_self_loop(
    net: PetriNet, start_place: PetriNet.Place, end_place: PetriNet.Place
):
    if start_place == end_place:
        place = start_place
        place_copy = clone_place(net, place, {})
        redo = copy(net.transitions)
        out_arcs = place.out_arcs
        for arc in list(out_arcs):
            target = arc.target
            pn_util.remove_arc(net, arc)
            add_arc_from_to(place_copy, target, net)
        do_transition = PetriNet.Transition(f"silent_do_{place.name}", None)
        do = set()
        do.add(do_transition)
        net.transitions.add(do_transition)
        add_arc_from_to(place, do_transition, net)
        add_arc_from_to(do_transition, place_copy, net)
        return do, redo, place, place_copy

    return None


def mine_loop(net: PetriNet, start_place: PetriNet.Place, end_place: PetriNet.Place):
    redo_subnet_transitions = get_reachable_transitions_from_place_to_another(
        end_place, start_place
    )

    if len(redo_subnet_transitions) == 0:
        return None, None

    do_subnet_transitions = get_reachable_transitions_from_place_to_another(
        start_place, end_place
    )

    if len(do_subnet_transitions) == 0:
        raise Exception("This should not be possible!")

    if do_subnet_transitions & redo_subnet_transitions:
        # This could happen if we have ->(..., Loop)
        return None, None

    if net.transitions != (do_subnet_transitions | redo_subnet_transitions):
        raise Exception("Something went wrong!")

    # A loop is detected: the set of transitions is partitioned into two disjoint, non-empty subsets (do and redo)
    return do_subnet_transitions, redo_subnet_transitions


def mine_xor(net: PetriNet, reachability_map):
    choice_branches = [{t} for t in net.transitions]

    for t1, t2 in combinations(net.transitions, 2):
        if t1 in reachability_map[t2] or t2 in reachability_map[t1]:
            new_branch = {t1, t2}
            choice_branches = __combine_parts(new_branch, choice_branches)

    if net.transitions != set().union(*choice_branches):
        raise Exception("This should not happen!")

    return choice_branches


def mine_partial_order(net, end_place, reachability_map):
    partition = [{t} for t in net.transitions]

    for place in net.places:
        out_size = len(place.out_arcs)
        if out_size > 1 or (place == end_place and out_size > 0):
            xor_branches = []
            for start_transition in pn_util.post_set(place):
                new_branch = {
                    node
                    for node in reachability_map[start_transition]
                    if isinstance(node, PetriNet.Transition)
                }
                xor_branches.append(new_branch)
            union_of_branches = set().union(*xor_branches)
            if place == end_place:
                not_in_every_branch = union_of_branches
            else:
                intersection_of_branches = set.intersection(*xor_branches)
                not_in_every_branch = union_of_branches - intersection_of_branches
            if len(not_in_every_branch) > 1:
                partition = __combine_parts(not_in_every_branch, partition)

    return partition


def __combine_parts(
    transitions_to_group_together: set[PetriNet.Transition],
    partition: list[set[PetriNet.Transition]],
):
    new_partition = []
    new_combined_group = set()

    for part in partition:

        if part & transitions_to_group_together:
            new_combined_group.update(part)
        else:
            new_partition.append(part)

    if new_combined_group:
        new_partition.append(new_combined_group)

    return new_partition
