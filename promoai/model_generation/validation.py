from typing import List as TList, Union

from pm4py.objects.powl.obj import (
    POWL,
    SilentTransition,
    StrictPartialOrder,
    Transition,
)


def validate_partial_orders_with_missing_transitive_edges(powl: POWL):
    if isinstance(powl, StrictPartialOrder):
        if not powl.order.is_irreflexive():
            raise Exception("The irreflexivity of the partial order is violated!")
        if not powl.order.is_transitive():
            powl.order.add_transitive_edges()
            if not powl.order.is_irreflexive():
                raise Exception(
                    "The transitive closure of the provided relation violates irreflexivity!"
                )
    if hasattr(powl, "children"):
        for child in powl.children:
            validate_partial_orders_with_missing_transitive_edges(child)


def validate_unique_transitions(
    powl: POWL,
) -> TList[Union[Transition, SilentTransition]]:
    def _find_duplicates(lst):
        counts = {}
        duplicates = []
        for item in lst:
            if item in counts:
                counts[item] += 1
                if counts[item] == 2:
                    duplicates.append(item)
            else:
                counts[item] = 1
        return duplicates

    def _collect_leaves(node: POWL):
        if isinstance(node, Transition) or isinstance(node, SilentTransition):
            return [node]

        elif hasattr(node, "children"):
            leaves = []
            for child in node.children:
                leaves = leaves + _collect_leaves(child)
            return leaves
        else:
            raise Exception(
                "Unknown model type! The following model is not a transition and has no children: "
                + str(node)
            )

    transitions = _collect_leaves(powl)
    duplicate_transitions = _find_duplicates(transitions)
    if len(duplicate_transitions) > 0:
        raise Exception(
            "Duplicate transitions! Each of the following transitions occurs in multiple submodels: "
            + str(
                [
                    t.label if t.label else "silent transition"
                    for t in duplicate_transitions
                ]
            )
        )
    return transitions
