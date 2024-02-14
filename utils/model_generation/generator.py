from utils.powl import Transition, SilentTransition, StrictPartialOrder, OperatorPOWL, Operator, POWL


# def check_frequency(model, optional, repeatable):
#     if repeatable:
#         if optional:
#             return OperatorPOWL(Operator.LOOP, [SilentTransition(), model])
#         else:
#             return OperatorPOWL(Operator.LOOP, [model, SilentTransition()])
#     else:
#         if optional:
#             return OperatorPOWL(Operator.XOR, [SilentTransition(), model])
#         else:
#             return model


class ModelGenerator:
    def __init__(self, enable_nested_partial_orders=False, copy_duplicates=False):
        self.used_as_submodel = []
        self.nested_partial_orders = enable_nested_partial_orders
        self.copy_duplicates = copy_duplicates
        pass

    def activity(self, label):
        return Transition(label)

    def create_model(self, node: POWL, parent_type):
        if node is None:
            res = SilentTransition()
        else:
            if isinstance(node, str):
                node = self.activity(node)
            elif not isinstance(node, POWL):
                raise Exception(
                    f"Only POWL models are accepted as submodels! You provide instead: {type(node)}.")
            if node in self.used_as_submodel:
                if self.copy_duplicates:
                    res = node.copy()
                else:
                    # raise Exception(f"Ensure that"
                    #                 f" each submodel is used uniquely!"
                    #                 f" Within the children of the this {parent_type} construct, you are trying to"
                    #                 f" reuse submodels that were used as children of other constructs (xor, loop,"
                    #                 f" or partial_order) before!")
                    raise Exception(f"Ensure that"
                                    f" each submodel is used uniquely! Avoid trying to"
                                    f" reuse submodels that were used as children of other constructs (xor, loop,"
                                    f" or partial_order) before!")
            else:
                res = node
        self.used_as_submodel.append(res)
        return res

    def xor(self, *args):
        if len(args) < 2:
            raise Exception("Cannot create an xor of less than 2 submodels!")
        children = [self.create_model(child, "'gen.xor'") for child in args]
        res = OperatorPOWL(Operator.XOR, children)
        return res

    def loop(self, do, redo):
        if do is None and redo is None:
            raise Exception("Cannot create an empty loop with both the do and redo parts missing!")
        children = [self.create_model(do, "'gen.loop'"), self.create_model(redo, "'gen.loop'")]
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
                raise Exception('Invalid dependencies for the partial order! You should provide a list that contains'
                                ' tuples of POWL models!')
        if len(list_children) < 2:
            raise Exception("Cannot create a partial order over less than 2 submodels!")
        children = dict()
        for child in list_children:
            new_child = self.create_model(child, "'gen.partial_order'")
            children[child] = new_child

        if self.nested_partial_orders:
            pass
        else:
            for child in children:
                if isinstance(child, StrictPartialOrder):
                    raise Exception("Do not use partial orders as 'direct children' of other partial orders."
                                    " Instead, combine dependencies at the same hierarchical level. Note that it is"
                                    " CORRECT to have 'partial_order > xor/loop > partial_order' in the hierarchy,"
                                    " while it is"
                                    " INCORRECT to have 'partial_order > partial_order' in the hierarchy.'")

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
