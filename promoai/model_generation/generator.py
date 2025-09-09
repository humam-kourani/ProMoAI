import powl
from powl.objects.obj import (
    Operator,
    OperatorPOWL,
    POWL,
    SilentTransition,
    StrictPartialOrder,
    Transition,
    DecisionGraph
)
from powl.objects.BinaryRelation import BinaryRelation
from collections import defaultdict
import networkx as nx

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
    def __init__(self, enable_nested_partial_orders=False, copy_duplicates=False, enable_nested_decision_graphs=False):
        self.used_as_submodel = []
        self.nested_partial_orders = enable_nested_partial_orders
        self.copy_duplicates = copy_duplicates
        self.nested_decision_graphs = enable_nested_decision_graphs

    def activity(self, label):
        return Transition(label)

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
                    res = node.copy()
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
        if self.nested_decision_graphs:
            pass
        else:
            for child in children:
                if isinstance(child, DecisionGraph):
                    raise Exception(
                        "Do not use decision graphs as 'direct children' of partial orders."
                        " Instead, combine dependencies at the same hierarchical level. Note that it is"
                        " INCORRECT to have 'partial_order > decision_graph' in the hierarchy.'"
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
        return res.simplify()
    def decision_graph(self, dependencies):
        list_children = []
        for dep in dependencies:
            if isinstance(dep, tuple):
                if len(dep) != 2:
                    raise Exception("Invalid dependency tuple in decision graph! Each tuple must contain exactly 2 elements.")
                for n in dep:
                    if n not in list_children:
                        list_children.append(n)
            elif isinstance(dep, POWL):
                if dep not in list_children:
                    list_children.append(dep)
            else:
                raise Exception(
                    "Invalid dependencies for the decision graph! You should provide a list that contains"
                    " tuples of POWL models!"
                )
        if len(list_children) <= 2:
            raise Exception("" \
            "A decision graph has at least a start and an end. The provided list has at least 2 elements."
            )
        children = dict()
        for child in list_children:
            new_child = self.create_model(child)
            children[child] = new_child
        # Identify start and end nodes first
        # Default dict with values 0
        incoming = defaultdict(lambda: 0)
        outgoing = defaultdict(lambda: 0)


        for dep in dependencies:
            if isinstance(dep, tuple):
                # Add both of them there
                outgoing[dep[0]] = outgoing.get(dep[0], 0) + 1
                incoming[dep[1]] = incoming.get(dep[1], 0) + 1
        start_nodes, end_nodes = [], []
        # Build a graph to check for edges
        G = nx.DiGraph()
        for child in children.keys():
            out_ = outgoing[child]
            in_ = incoming[child]
            if in_ == 0:
                start_nodes.append(child)
            if out_ == 0:
                end_nodes.append(child)
        # We have everything needed to create the decision graph
        binary_relation = BinaryRelation(list_children)
        for dep in dependencies:
            if isinstance(dep, tuple):
                for i in range(len(dep) - 1):
                    source = dep[i]
                    target = dep[i + 1]
                    if source in children.keys() and target in children.keys():
                        G.add_edge(source, target)
                        # Check for cycles
                        try:
                            nx.find_cycle(G, orientation='original')
                            raise Exception("Cycle detected in decision graph!")
                        except nx.exception.NetworkXNoCycle:
                            pass
                        binary_relation.add_edge(children[source], children[target])
        order = DecisionGraph(binary_relation, start_nodes, end_nodes)
        children = order.children
        if self.nested_decision_graphs:
            pass
        else:
            for child in children:
                if isinstance(child, DecisionGraph):
                    raise Exception(
                        "Do not use decision graphs as 'direct children' of other decision graphs."
                        " Instead, combine dependencies at the same hierarchical level in the same structure. Note that it is"
                        " CORRECT to have 'decision_graph > xor/loop > decision_graph in the hierarchy"
                    )
        if self.nested_partial_orders:
            pass
        else:
            for child in children:
                if isinstance(child, StrictPartialOrder):
                    raise Exception(
                        "Do not use partial orders as 'direct children' of decision graphs."
                        " Instead, combine dependencies at the same hierarchical level in the same structure by"
                        " integrating the partial order in the decision graph as additional dependencies in the decision graph."
                    )
        return order.simplify()



