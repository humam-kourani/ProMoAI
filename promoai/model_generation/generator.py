from copy import deepcopy

import networkx as nx

import powl
from powl.objects.BinaryRelation import BinaryRelation
from powl.objects.obj import (
    DecisionGraph,
    Operator,
    OperatorPOWL,
    POWL,
    SilentTransition,
    StrictPartialOrder,
    Transition,
)


def get_node_type(node):
    if node.__class__ is powl.objects.obj.Transition:
        return f"Activity ({node.label})"
    elif node.__class__ is powl.objects.obj.StrictPartialOrder:
        return "PartialOrder"
    elif node.__class__ is powl.objects.obj.OperatorPOWL:
        if node.operator is powl.objects.obj.Operator.XOR:
            return "XOR"
        elif node.operator is powl.objects.obj.Operator.LOOP:
            return "LOOP"
        else:
            return node.operator.value
    elif node.__class__ is powl.objects.obj.DecisionGraph:
        return "DecisionGraph"
    else:
        return node.__class__


class ModelGenerator:
    def __init__(
        self,
        enable_nested_partial_orders=True,
        copy_duplicates=False,
        enable_nested_decision_graphs=True,
    ):
        self.used_as_submodel = []
        self.nested_partial_orders = enable_nested_partial_orders
        self.copy_duplicates = copy_duplicates
        self.nested_decision_graphs = enable_nested_decision_graphs

    def activity(self, label, pool: str = None, lane: str = None):
        return Transition(label, organization=pool, role=lane)

    def silent_transition(self):
        return SilentTransition()

    def create_model(self, node: POWL):
        if node is None:
            res = SilentTransition()
        else:
            if isinstance(node, str):
                node = self.activity(node)
            elif not isinstance(node, POWL):
                raise Exception(
                    f"Only POWL models are accepted as submodels! You provide instead: {type(node)}."
                )
            if node in self.used_as_submodel:
                if self.copy_duplicates:
                    res = deepcopy(node)
                else:
                    node_type = get_node_type(node)
                    raise Exception(
                        f"Ensure that"
                        f" each submodel is used uniquely! Avoid trying to"
                        f" reuse submodels that were used as children of other constructs (xor, loop,"
                        f" or partial_order) before! The error occured when trying to reuse a node of type {node_type}."
                    )
            else:
                res = node
        self.used_as_submodel.append(res)
        return res

    def xor(self, *args):
        if len(args) < 2:
            raise Exception("Cannot create an xor of less than 2 submodels!")
        children = [self.create_model(child) for child in args]
        res = OperatorPOWL(Operator.XOR, children)
        return res

    def loop(self, do, redo):
        if do is None and redo is None:
            raise Exception(
                "Cannot create an empty loop with both the do and redo parts missing!"
            )
        children = [self.create_model(do), self.create_model(redo)]
        res = OperatorPOWL(Operator.LOOP, children)
        return res

    def partial_order(self, dependencies):
        list_children = []
        for dep in dependencies:
            if isinstance(dep, tuple):
                for n in dep:
                    if n not in list_children:
                        list_children.append(n)
            elif isinstance(dep, POWL):
                if dep not in list_children:
                    list_children.append(dep)
            else:
                raise Exception(
                    "Invalid dependencies for the partial order! You should provide a list that contains"
                    " tuples of POWL models!"
                )
        if len(list_children) == 1:
            return list_children[0]
        if len(list_children) == 0:
            raise Exception("Cannot create a partial order over 0 submodels!")
        children = dict()
        for child in list_children:
            new_child = self.create_model(child)
            children[child] = new_child

        if self.nested_partial_orders:
            pass
        else:
            for child in children:
                if isinstance(child, StrictPartialOrder):
                    raise Exception(
                        "Do not use partial orders as 'direct children' of other partial orders."
                        " Instead, combine dependencies at the same hierarchical level. Note that it is"
                        " CORRECT to have 'partial_order > xor/loop > partial_order' in the hierarchy,"
                        " while it is"
                        " INCORRECT to have 'partial_order > partial_order' in the hierarchy.'"
                    )
        order = StrictPartialOrder(list(children.values()))
        for dep in dependencies:
            if isinstance(dep, tuple):
                for i in range(len(dep) - 1):
                    source = dep[i]
                    target = dep[i + 1]
                    if source in children.keys() and target in children.keys():
                        order.add_edge(children[source], children[target])

        res = order
        return res

    def decision_graph(self, dependencies):
        list_children = []
        for dep in dependencies:
            if isinstance(dep, tuple):
                if len(dep) != 2:
                    raise Exception(
                        "Invalid dependency tuple in decision graph! Each tuple must contain exactly 2 elements."
                    )
                for n in dep:
                    if n not in list_children and n is not None:
                        list_children.append(n)
            elif isinstance(dep, POWL):
                if dep not in list_children:
                    list_children.append(dep)
            else:
                raise Exception(
                    "Invalid dependencies for the decision graph! You should provide a list that contains"
                    " tuples of POWL models!"
                )
        if len(list_children) < 1:
            raise Exception(
                ""
                "A decision graph has at least one node. The provided list should comprise of at least one element."
            )

        children = dict()
        for child in list_children:
            new_child = self.create_model(child)
            children[child] = new_child
        # Identify start and end nodes first
        # Default dict with values 0
        start_nodes, end_nodes = [], []
        empty_path = False

        for dep in dependencies:
            if isinstance(dep, tuple):
                # Add both of them there
                if len(dep) != 2:
                    raise Exception(
                        "Invalid dependency tuple in decision graph! Each tuple must contain exactly 2 elements. "
                        "Note that None can be used to indicate start or end."
                    )
                source = dep[0]
                target = dep[1]
                if source is None and target is None:
                    empty_path = True
                elif source is None:
                    start_nodes.append(children[target])
                elif target is None:
                    end_nodes.append(children[source])

        # Build a graph to check for edges
        G = nx.DiGraph()
        # Add artificial start and end nodes
        G.add_node("ArtificialStart")
        G.add_node("ArtificialEnd")
        for sn in start_nodes:
            G.add_edge("ArtificialStart", sn)
        for en in end_nodes:
            G.add_edge(en, "ArtificialEnd")
        if empty_path:
            G.add_edge("ArtificialStart", "ArtificialEnd")
        # We have everything needed to create the decision graph
        binary_relation = BinaryRelation(list_children)
        for dep in dependencies:
            if isinstance(dep, tuple):
                for i in range(len(dep) - 1):
                    source = dep[i]
                    target = dep[i + 1]
                    if source in children.keys() and target in children.keys():
                        G.add_edge(source, target)
                        binary_relation.add_edge(children[source], children[target])
        # Check if all nodes are from start to end
        for node in list_children:
            if not (
                nx.has_path(G, "ArtificialStart", node)
                and nx.has_path(G, node, "ArtificialEnd")
            ):
                raise Exception(
                    f"All nodes in a decision graph must be on a path from a start node to an end node, {children[node]} isn't!"
                )
        order = DecisionGraph(
            binary_relation, start_nodes, end_nodes, empty_path=empty_path
        )
        children = order.children
        if self.nested_decision_graphs:
            pass
        else:
            for child in children:
                if isinstance(child, DecisionGraph):
                    raise Exception(
                        "Do not use decision graphs as 'direct children' of other decision graphs."
                        " Instead, combine dependencies at the same hierarchical level in the same structure. Note that it is"
                        " CORRECT to have 'decision_graph > xor/loop/partial_order > decision_graph in the hierarchy"
                    )
        return order

    def self_loop(self, node: POWL):
        if node is None:
            raise Exception("Cannot create a self-loop over an empty model!")
        child = self.create_model(node)
        silent = SilentTransition()
        return OperatorPOWL(Operator.LOOP, [child, silent])

    def skip(self, node: POWL):
        if node is None:
            raise Exception("Cannot create a skip over an empty model!")
        child = self.create_model(node)
        silent = SilentTransition()
        return OperatorPOWL(Operator.XOR, [child, silent])

    @staticmethod
    def copy(node: POWL):
        return deepcopy(node)
