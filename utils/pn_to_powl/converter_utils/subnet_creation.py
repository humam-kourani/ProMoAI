from typing import Union, Set
from pm4py.objects.petri_net.obj import PetriNet
from pm4py.objects.powl.obj import Transition, SilentTransition
from pm4py.objects.petri_net.utils import petri_utils as pn_util


def id_generator():
    count = 1
    while True:
        yield f"id{count}"
        count += 1


def clone_place(net, place, node_map):
    cloned_place = PetriNet.Place(f"{place.name}_cloned")
    net.places.add(cloned_place)
    node_map[place] = cloned_place
    return cloned_place


def clone_transition(net, transition, node_map):
    cloned_transition = PetriNet.Transition(f"{transition.name}_cloned", transition.label)
    net.transitions.add(cloned_transition)
    node_map[transition] = cloned_transition
    return cloned_transition


def clone_subnet(net: PetriNet, subnet_transitions: Set[PetriNet.Transition],
                 start_place: PetriNet.Place, end_place: PetriNet.Place):
    subnet_net = PetriNet(f"Subnet_{next(id_generator())}")
    node_map = {}

    for node in subnet_transitions:
        clone_transition(subnet_net, node, node_map)

    # Add arcs and remaining places of the subnet
    for arc in net.arcs:
        source = arc.source
        target = arc.target
        if source in subnet_transitions or target in subnet_transitions:
            if source in node_map.keys():
                cloned_source = node_map[source]
            else:
                cloned_source = clone_place(subnet_net, source, node_map)
            if target in node_map.keys():
                cloned_target = node_map[target]
            else:
                cloned_target = clone_place(subnet_net, target, node_map)
            add_arc_from_to(cloned_source, cloned_target, subnet_net)

    mapped_start_place = node_map[start_place]
    mapped_end_place = node_map[end_place]

    return subnet_net, mapped_start_place, mapped_end_place


def locally_identical(p1, p2, transitions):
    pre1 = pn_util.pre_set(p1) & transitions
    pre2 = pn_util.pre_set(p2) & transitions
    post1 = pn_util.post_set(p1) & transitions
    post2 = pn_util.post_set(p2) & transitions
    return pre1 == pre2 and post1 == post2


def apply_partial_order_projection(net: PetriNet, subnet_transitions: Set[PetriNet.Transition],
                                   start_places: Set[PetriNet.Place], end_places: Set[PetriNet.Place]):
    subnet_net = PetriNet(f"Subnet_{next(id_generator())}")
    node_map = {}

    for node in subnet_transitions:
        clone_transition(subnet_net, node, node_map)

    list_start_places = list(start_places)
    old_start = list_start_places[0]
    for place in list_start_places[1:]:
        if not locally_identical(place, old_start, subnet_transitions):
            raise Exception("Unique local start property is violated!")
    new_start_place = clone_place(subnet_net, old_start, node_map)
    node_map[old_start] = new_start_place

    if start_places == end_places:
        new_end_place = new_start_place
    else:
        list_end_places = list(end_places)
        old_end = list_end_places[0]
        for place in list_end_places[1:]:
            if not locally_identical(place, old_end, subnet_transitions):
                raise Exception("Unique local end property is violated!")
        new_end_place = clone_place(subnet_net, old_end, node_map)
        node_map[old_end] = new_end_place

    # Add arcs and remaining places of the subnet
    for arc in net.arcs:
        source = arc.source
        target = arc.target
        if source in subnet_transitions or target in subnet_transitions:
            if source in node_map.keys():
                cloned_source = node_map[source]
            else:
                if source in start_places or source in end_places:
                    continue
                cloned_source = clone_place(subnet_net, source, node_map)
            if target in node_map.keys():
                cloned_target = node_map[target]
            else:
                if target in start_places or target in end_places:
                    continue
                cloned_target = clone_place(subnet_net, target, node_map)
            add_arc_from_to(cloned_source, cloned_target, subnet_net)

    return subnet_net, new_start_place, new_end_place


def add_arc_from_to(source: Union[PetriNet.Place, PetriNet.Transition],
                    target: Union[PetriNet.Transition, PetriNet.Place], net: PetriNet):
    arc = PetriNet.Arc(source, target)
    net.arcs.add(arc)
    source.out_arcs.add(arc)
    target.in_arcs.add(arc)


def pn_transition_to_powl(transition: PetriNet.Transition) -> Transition:
    label = transition.label
    if label:
        return Transition(label=label)
    else:
        return SilentTransition()
