from itertools import combinations

from pm4py import PetriNet
from pm4py.objects.petri_net.utils import petri_utils as pn_util
from pm4py.algo.analysis.workflow_net import algorithm as wf_eval

from utils.pn_to_powl.converter_utils.subnet_creation import add_arc_from_to, id_generator


def validate_workflow_net(net: PetriNet):
    places_no_incoming = [p for p in net.places if not p.in_arcs]
    if len(places_no_incoming) == 1:
        start_place = places_no_incoming[0]
    else:
        raise Exception(f"Not a WF-net!")

    places_no_outgoing = [p for p in net.places if not p.out_arcs]
    if len(places_no_outgoing) == 1:
        end_place = places_no_outgoing[0]
    else:
        raise Exception(f"Not a WF-net!")

    if not wf_eval.apply(net):
        raise Exception(f"Not a WF-net!")

    return start_place, end_place


def remove_initial_and_end_silent_activities(net: PetriNet, start_places: set[PetriNet.Place],
                                             end_places: set[PetriNet.Place]):
    change = True
    while change and len(net.transitions) > 1:
        change = False
        if len(start_places) == 1:
            start_place = list(start_places)[0]
            if len(start_place.in_arcs) == 0 and len(start_place.out_arcs) == 1:
                transition = list(start_place.out_arcs)[0].target
                if len(transition.in_arcs) == 1 and is_silent(transition):
                    pn_util.remove_place(net, start_place)
                    start_places.remove(start_place)
                    next_places = list(pn_util.post_set(transition))
                    pn_util.remove_transition(net, transition)
                    for p in next_places:
                        start_places.add(p)
                    change = True

    change = True
    while change and len(net.transitions) > 1:
        change = False
        if len(end_places) == 1:
            end_place = list(end_places)[0]
            if len(end_place.in_arcs) == 1 and len(end_place.out_arcs) == 0:
                transition = list(end_place.in_arcs)[0].source
                if len(transition.out_arcs) == 1 and is_silent(transition):
                    pn_util.remove_transition(net, transition)
                    pn_util.remove_place(net, end_place)
                    end_places.remove(end_place)
                    prev_places = list(pn_util.pre_set(transition))
                    for p in prev_places:
                        end_places.add(p)
                    change = True

    return start_places, end_places


def __get_identical_place(place: PetriNet.Place, places_set: set[PetriNet.Place]):
    for other in places_set:
        if (pn_util.post_set(place) == pn_util.post_set(other)
                and pn_util.pre_set(place) == pn_util.pre_set(other)):
            return other
    return None


def __remove_and_replace_if_present(old_p: PetriNet.Place, new_p: PetriNet.Place, place_set: set[PetriNet.Place]):
    if old_p in place_set:
        place_set.remove(old_p)
        if new_p not in place_set:
            place_set.add(new_p)
    return place_set


def remove_duplicated_places(net: PetriNet, start_places: set[PetriNet.Place], end_places: set[PetriNet.Place]):
    all_places = list(net.places)
    places_to_keep = {all_places[0]}
    for place in all_places[1:]:
        other = __get_identical_place(place, places_to_keep)
        if other:
            pn_util.remove_place(net, place)
            start_places = __remove_and_replace_if_present(place, other, start_places)
            end_places = __remove_and_replace_if_present(place, other, end_places)
        else:
            places_to_keep.add(place)

    return start_places, end_places


def remove_unconnected_places(net: PetriNet, start_places: set[PetriNet.Place], end_places: set[PetriNet.Place]):
    places = list(net.places)
    for p in places:
        if len(p.in_arcs) == 0 == len(p.out_arcs):
            pn_util.remove_place(net, p)
            start_places.remove(p)
            end_places.remove(p)

    return start_places, end_places


def preprocess(net):
    all_places = net.places
    for p1, p2 in combinations(all_places, 2):
        pre1 = pn_util.pre_set(p1)
        pre2 = pn_util.pre_set(p2)
        post1 = pn_util.post_set(p1)
        post2 = pn_util.post_set(p2)

        if (pre1 == pre2) and (post1 == post2):
            pn_util.remove_place(net, p2)
            return preprocess(net)

        if pre1 == pre2:
            common_post = post1 & post2
            if len(pre1) > 1 or len(common_post) > 0:
                new_place = PetriNet.Place(f"place_{next(id_generator())}")
                net.places.add(new_place)

                for transition in pre1:
                    add_arc_from_to(transition, new_place, net)
                    arcs_to_remove = p1.in_arcs | p2.in_arcs
                    for arc in arcs_to_remove:
                        pn_util.remove_arc(net, arc)

                for transition in common_post:
                    add_arc_from_to(new_place, transition, net)
                    out_arcs = p1.out_arcs | p2.out_arcs
                    for arc in out_arcs:
                        if arc.target in common_post:
                            pn_util.remove_arc(net, arc)

                new_silent = PetriNet.Transition(f"silent_transition_{next(id_generator())}")
                net.transitions.add(new_silent)
                add_arc_from_to(new_place, new_silent, net)
                add_arc_from_to(new_silent, p1, net)
                add_arc_from_to(new_silent, p2, net)
                return preprocess(net)

        if post1 == post2:
            common_pre = pre1 & pre2
            if len(post1) > 1 or len(common_pre) > 0:
                new_place = PetriNet.Place(f"place_{next(id_generator())}")
                net.places.add(new_place)

                for transition in post1:
                    add_arc_from_to(new_place, transition, net)
                    arcs_to_remove = p1.out_arcs | p2.out_arcs
                    for arc in arcs_to_remove:
                        pn_util.remove_arc(net, arc)

                for transition in common_pre:
                    add_arc_from_to(transition, new_place, net)
                    in_arcs = p1.in_arcs | p2.in_arcs
                    for arc in in_arcs:
                        if arc.source in common_pre:
                            pn_util.remove_arc(net, arc)

                new_silent = PetriNet.Transition(f"silent_transition_{next(id_generator())}")
                net.transitions.add(new_silent)
                add_arc_from_to(p1, new_silent, net)
                add_arc_from_to(p2, new_silent, net)
                add_arc_from_to(new_silent, new_place, net)

                return preprocess(net)

    return net


def add_new_start_and_end_if_needed(net, start_places: set[PetriNet.Place], end_places: set[PetriNet.Place]):
    if len(start_places) == 0 or len(end_places) == 0:
        raise Exception("This should not happen!")

    if len(start_places) > 1:

        new_source_id = f"source_{next(id_generator())}"
        new_source = __redirect_shared_arcs_to_new_place(net, list(start_places), new_source_id)

        if new_source:

            new_silent = PetriNet.Transition(f"silent_start_{next(id_generator())}")
            net.transitions.add(new_silent)

            for p in start_places:
                add_arc_from_to(new_silent, p, net)

            add_arc_from_to(new_source, new_silent, net)
            start_places = {new_source}

    if len(end_places) > 1:

        new_sink_id = f"sink_{next(id_generator())}"
        new_sink = __redirect_shared_arcs_to_new_place(net, list(end_places), new_sink_id)

        if new_sink:

            new_silent = PetriNet.Transition(f"silent_end_{next(id_generator())}")
            net.transitions.add(new_silent)

            for p in end_places:
                add_arc_from_to(p, new_silent, net)

            add_arc_from_to(new_silent, new_sink, net)

            end_places = {new_sink}

    return start_places, end_places


def __redirect_shared_arcs_to_new_place(net, places: list[PetriNet.Place], new_place_id):
    shared_pre_set = set(pn_util.pre_set(places[0]))
    for p in places[1:]:
        shared_pre_set &= set(pn_util.pre_set(p))

    shared_post_set = set(pn_util.post_set(places[0]))
    for p in places[1:]:
        shared_post_set &= set(pn_util.post_set(p))

    arcs = list(net.arcs)

    for arc in arcs:
        source = arc.source
        target = arc.target
        if (source in shared_pre_set and target in places) \
                or (source in places and target in shared_post_set): \
                pn_util.remove_arc(net, arc)

    if len(shared_post_set) > 0 or len(shared_pre_set) > 0:
        new_place = PetriNet.Place(new_place_id)
        net.places.add(new_place)

        for node in shared_pre_set:
            add_arc_from_to(node, new_place, net)

        for node in shared_post_set:
            add_arc_from_to(new_place, node, net)

        return new_place

    else:
        return None


def is_silent(transition) -> bool:
    return transition.label is None
