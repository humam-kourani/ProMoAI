import inspect
from typing import List

from utils.prompting.shots import SHOTS

import_statement = 'from utils.model_generation import ModelGenerator'


def add_role():
    return "Your role: you are an expert in process modeling," \
           " familiar with common" \
           " process constructs such as exclusive choice, do-redo loops, and partial orders." \
           " Your task is to analyze the textual description of a process and transform it into a process model in" \
           " the POWL language. When generating a model, be as precise" \
           " as possible and capture all details of the process in the model. Also act as the process owner and use" \
           " your expertise and familiarity with the" \
           " process context to fill in any missing knowledge. \n\n"


def add_knowledge():
    return "Use the following knowledge about the POWL process modeling language:\n" \
           "A POWL model is a hierarchical model. POWL models are recursively generated" \
           " by combining submodels into a new model either using an operator (xor or loop)" \
           " or as a partial order. " \
           " We define three types of POWL models. The first type of POWL models is the base case consisting of a" \
           " single activity. For the second type" \
           " of POWL models, we use an operator (xor or loop) to combine" \
           " multiple POWL models into a new model. We use xor to model an exclusive choice" \
           " of n >= 2 sub-models. We use the operator loop to model a do-redo loop of 2 POWL models." \
           " The third type of POWL models is defined as a partial" \
           " order over n >= 2 submodels. A partial order is binary relation that is irreflexive, transitive," \
           " and asymmetry. \n\n"


def add_least_to_most():
    return "Provide the Python code that " \
           "recursively generate a POWL model. Save the final model is the" \
           " variable 'final_model'. Do not try to execute the code, just return it. Assume the class ModelGenerator" \
           " is properly implemented and can be imported using the import statement:" \
           f" {import_statement}. ModelGenerator provides the functions" \
           " described below:\n" \
           " - activity(label) generates an activity. It takes 1 string arguments," \
           " which is the label of the activity.\n" \
           " - xor(*args) takes n >= 2 arguments, which are the submodels. Use it to model an exclusive choice" \
           " structures, i.e., if you have several possible paths where only one of them can be taken (either or), then" \
           "you use xor to combine them. If a decision is made based on some condition at some" \
           " point in a process, you should model an exclusive choice between the two paths starting after this" \
           " decision xor(path_1 path_2) where path_1 and path_2 are subprocess that encapsulates the full sequence" \
           " of actions following each decision. You can use xor(submodel, None) to make a submodel optional; " \
           "i.e., to model an" \
           "exclusive choice between executing this submodel or skipping it.\n" \
           " - loop(do, redo) takes 2 arguments, which are the do and redo parts. Use it to model cyclic" \
           " behavior; i.e., the do part is executed once first, and every time the redo part is executed, it" \
           " is followed by another execution of the do part. You" \
           " can also use loop to model a self-loop by setting the redo part to None; i.e., to indicate that the do part" \
           " can be repeated from 1 to as many times as possible. You can also model a skippable self-loop by" \
           " setting the do part to None instead; i.e., to indicate that the redo part can be repeated from 0 to" \
           " as many times as possible. You can use a self-loop to model that in a complicated process you can go back" \
           " to certain initial stage: first you model the complicated process, then you put it inside a loop.\n" \
           " - partial_order(dependencies) takes 1 argument, which is a list of tuples of submodels. These tuples" \
           " set the nodes of the partial order and specify the" \
           " edges of the partial order (i.e., the sequential dependencies). The" \
           " transitive closure of the added dependencies should conform with the irreflexivity" \
           " requirement of partial orders. We interpret unconnected nodes in a partial order to be" \
           " concurrent and connections between nodes as sequential dependencies. Use a partial order" \
           " with no edges (with the parameter 'dependencies' set to a list of tuples of size 1) to model pure" \
           " concurrency/independency; i.e., to model the relation " \
           " between sub models that can all be happens at the same time/in any order. However, note that all of them" \
           " need to happen unlike the xor case. The main difference is that with xor case you model alternative" \
           " paths (either path_1 or path_2), while with a partial order you model concurrent paths (you do both" \
           " path_1 and path_2). The general assumption is partial orders is that nodes are concurrent; however, you can" \
           " still add sequential dependencies between certain nodes (as tuples in the list for the parameter" \
           " 'dependencies'). For example, this is" \
           " the case in systems where you execute all subprocesses but one of them must be completed before" \
           " starting another one. Assume we have 4 submodel A, B, C, D. partial_order(dependencies=[(A, B), (B, C), (C, D)]) " \
           "models a sequence A -> B -> C -> D; partial_order(dependencies=[(A,), (B,), (C,), (D,)]) models full" \
           " concurrency; partial_order(dependencies=[(A,B), (C,), (D,)]) models" \
           " concurrency with the sequential dependency A -> B. Avoid using a partial" \
           " order as a child of" \
           " another partial order to ensure not leaving out any sequential dependencies. To resolve this," \
           " you can combine the two orders.\n" \
           "Note: for any powl model, you can always call powl.copy() to create another instance" \
           " of the same model. This is useful to model cases where a subporcess or activity can be executed exactly" \
           "twice (not really in a loop). \n\n"


def add_process_description(process_description):
    return "This is the process description: " + process_description


def self_evaluation():
    return "Avoid common mistakes. " \
           "First, ensure that the transitive closure of the generated partial orders" \
           " do not violate irreflexivity. Verify that all optional/skippable and" \
           " repeatable parts are modeled correctly. Also validate that the same submodel" \
           " is not used multiple times (e.g., in xor then in partial_oder)! You have three ways for avoiding" \
           " this depending on the case: (1)" \
           " consider using loops to model cyclic behaviour; (2) if you instead want to create a second instance" \
           " of the same submodel, consider creating a copy of it; (3) if none of these two cases apply, then" \
           " your structure is not correct. Ensure that you correctly model xor/loop between larger complete" \
           " alternative/loop paths (i.e., between full paths, not decision points). Finally, do not create partial" \
           " orders as children of other partial orders. " \
           " Instead, combine dependencies at the same hierarchical level to avoid nested partial orders." \
           " Example of Correct Use of Partial Order:\n" \
           "```python\n" \
           "poset = partial_order(dependencies=[(A, B), (B, C)])\n" \
           "```\n\n" \
           "Example of Incorrect Use of Partial Order:\n" \
           "```python\n" \
           "poset_1 partial_order(dependencies=[(B, C)])\n" \
           "poset_2 = partial_order(dependencies=[(A, poset)])\n" \
           "```\n\n"


def code_generation():
    return "At the end of your response provide a single Python code snippet (i.e., staring with '```python') that" \
           " contains the full final code. \n\n"


def add_few_shots():
    res = "Please use few-shots learning. These are few illustrating shots extended with common errors that you" \
          " should avoid for each example:\n"
    for i in range(len(SHOTS)):
        description, model, errors = SHOTS[i]
        full_source = inspect.getsource(model)
        source_lines = full_source.split('\n')
        content_lines = source_lines[1:-2] + ['\n']
        content_as_string = '\n'.join(line[4:] for line in content_lines)
        res = res + f'Process description for example {i + 1}:\n{description}\n'
        res = res + f'Process model for example {i + 1}:\n'
        res = res + f'```python\n{import_statement}\n{content_as_string}'
        res = res + f'```\n'
        res = res + f'Common errors to avoid for example {i + 1}:\n{errors}\n'
    return res + '\n'


def create_model_generation_prompt(process_description: str) -> str:
    prompt = add_role()
    prompt = prompt + add_knowledge()
    prompt = prompt + add_least_to_most()
    prompt = prompt + self_evaluation()
    prompt = prompt + add_few_shots()
    prompt = prompt + code_generation()
    prompt = prompt + add_process_description(process_description)

    return prompt


def create_conversation(process_description: str) -> List[dict[str:str]]:
    prompt = create_model_generation_prompt(process_description)
    conversation = [{"role": "user", "content": f'{prompt}'}]
    print(prompt)
    return conversation


def update_conversation(conversation: List[dict[str:str]], feedback: str) -> List[dict[str:str]]:
    update_prompt = "Please update the model to fix it based on the provided feedback. Please make sure the returned" \
                    " model matches the initial process description, all previously provided feedback, and the new" \
                    "feedback comment as well. Make sure to save the updated final model is the variable" \
                    " 'final_model'. This is the new feedback comment:" + feedback
    conversation.append({"role": "user", "content": f'{update_prompt}'})
    print(update_prompt)
    return conversation
