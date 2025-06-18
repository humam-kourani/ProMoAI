def add_prompt_strategies(
    model_abstraction="simplified_xml",
    enable_role_prompting=True,
    enable_natural_language_restriction=True,
    enable_chain_of_thought=False,
    enable_process_analysis=False,
    enable_knowledge_injection=False,
    enable_few_shots_learning=False,
    enable_negative_prompting=False,
    enable_examples=True,
):

    prompt = ""

    if enable_role_prompting:
        role_prompt = role_prompting()
        prompt += role_prompt

    if enable_process_analysis:
        proc_anal = role_prompting_process_expert()
        prompt += proc_anal

    if enable_natural_language_restriction:
        nlp_restriction = natural_language_restriction()
        prompt += nlp_restriction

    if enable_chain_of_thought:
        ch_of_thought = chain_of_thoughts()
        prompt += ch_of_thought

    if enable_knowledge_injection:
        know_inj = knowledge_injection()
        prompt += know_inj

    if enable_examples:
        examples = get_examples()
        prompt += examples
    elif model_abstraction in ["json", "simplified_xml"]:
        if enable_few_shots_learning:
            if model_abstraction == "json":
                abstraction = process_textual_representation_json
            elif model_abstraction == "simplified_xml":
                abstraction = process_textual_representation_simplified_xml
            few_shots = few_shots_learning_json(abstraction)
            prompt += few_shots

            if enable_negative_prompting:
                negative_prompt = negative_prompting_json()
                prompt += negative_prompt

        elif enable_negative_prompting:
            if model_abstraction == "json":
                abstraction = process_textual_representation_json
            elif model_abstraction == "simplified_xml":
                abstraction = process_textual_representation_simplified_xml
            negative_prompt = negative_prompting_with_questions(abstraction)
            prompt += negative_prompt

    return prompt


def role_prompting():
    return "- Your role: You are an expert in business process modeling and the BPMN 2.0 standard. I will give you a textual representation of a full BPMN model (and also potentially a selection of a subset of elements) and ask you questions about the process. You are supposed to answer the questions based on your understanding of the provided model.\n\n"


# from https://en.wikipedia.org/wiki/Business_Process_Model_and_Notation
def knowledge_injection():
    return """
- Business Process Model and Notation (BPMN) is a standardized graphical notation for modeling business processes.\n
- BPMN's four basic element categories are:\n
1. Flow objects: Events, activities, gateways\n
2. Connecting objects: Sequence flow, message flow, association\n
3. Swim lanes: Pool, lane, Dark Pool\n
4. Artifacts: Data object, group, annotation\n
- Event: An Event is represented with a circle and denotes something that happens (compared with an activity, which is something that is done). Icons within the circle denote the type of event (e.g., an envelope representing a message, or a clock representing time). Events are also classified as Catching (for example, if catching an incoming message starts a process) or Throwing (such as throwing a completion message when a process ends).\n
1. Start event: Acts as a process trigger; indicated by a single narrow border, and can only be Catch, so is shown with an open (outline) icon.\n
2. Intermediate event: Represents something that happens between the start and end events; is indicated by a double border, and can Throw or Catch (using solid or open icons as appropriate). For example, a task could flow to an event that throws a message across to another pool, where a subsequent event waits to catch the response before continuing.\n
3. End event: Represents the result of a process; indicated by a single thick or bold border, and can only Throw, so is shown with a solid icon.\n
- Activity: An activity is represented with a rounded-corner rectangle and describes the kind of work which must be done. An activity is a generic term for work that a company performs. It can be atomic or compound.\n
1. Task: A task represents a single unit of work that is not or cannot be broken down to a further level of business process detail. It is referred to as an atomic activity. A task is the lowest level activity illustrated on a process diagram. A set of tasks may represent a high-level procedure.\n
2. Sub-process: Used to hide or reveal additional levels of business process detail. When collapsed, a sub-process is indicated by a plus sign against the bottom line of the rectangle; when expanded, the rounded rectangle expands to show all flow objects, connecting objects, and artifacts. A sub-process is referred to as a compound activity. A sub-process has its own self-contained start and end events; sequence flows from the parent process must not cross the boundary.\n
3. Transaction: A form of sub-process in which all contained activities must be treated as a whole; i.e., they must all be completed to meet an objective, and if any one of them fails, they must all be compensated (undone). Transactions are differentiated from expanded sub-processes by being surrounded by a double border.\n
4. Call Activity: A point in the process where a global process or a global Task is reused. A call activity is differentiated from other activity types by a bolded border around the activity area.\n
- Gateway: A gateway is represented with a diamond shape and determines forking and merging of paths, depending on the conditions expressed.\n
1. Exclusive: Used to create alternative flows in a process. Because only one of the paths can be taken, it is called exclusive.\n
2. Event Based: The condition determining the path of a process is based on an evaluated event.\n
3. Parallel: Used to create parallel paths without evaluating any conditions.\n
4. Inclusive: Used to create alternative flows where all paths are evaluated.\n
5. Exclusive Event Based: An event is being evaluated to determine which of mutually exclusive paths will be taken.\n
6. Complex: Used to model complex synchronization behavior.\n
7. Parallel Event Based: Two parallel processes are started based on an event, but there is no evaluation of the event.\n
- Connections: Flow objects are connected to each other using Connecting objects, which are of three types: sequences, messages, and associations.\n
1. Sequence Flow: A Sequence Flow is represented with a solid line and arrowhead, and shows in which order the activities are performed. The sequence flow may also have a symbol at its start, a small diamond indicates one of a number of conditional flows from an activity, while a diagonal slash indicates the default flow from a decision or activity with conditional flows.\n
2. Message Flow: A Message Flow is represented with a dashed line, an open circle at the start, and an open arrowhead at the end. It tells us what messages flow across organizational boundaries (i.e., between pools). A message flow can never be used to connect activities or events within the same pool.\n
3. Association: An Association is represented with a dotted line. It is used to associate an Artifact or text to a Flow Object, and can indicate some directionality using an open arrowhead (toward the artifact to represent a result, from the artifact to represent an input, and both to indicate it is read and updated). No directionality is used when the Artifact or text is associated with a sequence or message flow (as that flow already shows the direction).\n
- Swim lanes are a visual mechanism of organising and categorising activities, based on cross functional flowcharting, and in BPMN consist of two types:\n
- Pool: Represents major participants in a process, typically separating different organisations. A pool contains one or more lanes (like a real swimming pool). A pool can be open (i.e., showing internal detail) when it is depicted as a large rectangle showing one or more lanes, or collapsed (i.e., hiding internal detail) when it is depicted as an empty rectangle stretching the width or height of the diagram.\n
- Lane: Used to organise and categorise activities within a pool according to function or role, and depicted as a rectangle stretching the width or height of the pool. A lane contains the flow objects, connecting objects and artifacts.\n
- Artifacts: Artifacts allow developers to bring some more information into the model/diagram. In this way the model/diagram becomes more readable. There are three pre-defined Artifacts, and they are:\n
1. Data objects: Data objects show the reader which data is required or produced in an activity.\n
2. Group: A Group is represented with a rounded-corner rectangle and dashed lines. The group is used to group different activities but does not affect the flow in the diagram.\n
3. Annotation: An annotation is used to give the reader of the model/diagram an understandable impression.\n\n\n"""


def natural_language_restriction():
    return (
        "- Please answer in natural language, so that any user not familiar with the BPMN standard can understand your answer without any technical knowledge; i.e., avoid IDs or technical terms like Task, Gate, flow, lane, etc.; rather use natural language to describe the behavior of the underlying process.\n\n"
        " Please give short, compact answers.\n\n"
        " Please use the same language as the one used by the user in the last question question.\n\n"
    )


def chain_of_thoughts():
    return "- Where possible (especially for complex queries), please share the chain of thoughts or reasoning behind your answers. This helps in understanding how you arrived at your conclusion.\n\n"


def role_prompting_process_expert():
    return "- Please take the role of a process expert who is familiar with the domain of the provided process, and use your domain knowledge to better understand and analyze the process, filling in any missing gaps.\n\n"


# for the model credit-scoring-asynchronous.bpmn from https://github.com/camunda/bpmn-for-research
process_textual_representation_json = """- { $type: bpmn:Collaboration, id: Collaboration_1y0blh3, participants: [object Object],[object Object],[object Object], messageFlows: [object Object],[object Object],[object Object],[object Object],[object Object],[object Object],[object Object], $parent: Definitions_1 }
- { $type: bpmn:Participant, id: Participant_1x9zkso, name: credit scoring frontend (bank), processRef: Process_1, $parent: Collaboration_1y0blh3 }
- { $type: bpmn:Participant, id: Participant_0e81yis, name: credit scoring (bank), processRef: Process_0hiditg, $parent: Collaboration_1y0blh3 }
- { $type: bpmn:Task, id: Task_16winvj, name: request credit score, $parent: Process_0hiditg }
- { $type: bpmn:ExclusiveGateway, id: ExclusiveGateway_11dldcm, $parent: Process_0hiditg }
- { $type: bpmn:Task, id: Task_1fzfxey, name: send credit score, $parent: Process_0hiditg }
- { $type: bpmn:EndEvent, id: EndEvent_0rp5trg, name: scoring request handled, eventDefinitions: , $parent: Process_0hiditg }
- { $type: bpmn:EndEvent, id: EndEvent_0rp5trg, name: scoring request handled, eventDefinitions: , $parent: Process_0hiditg }
- { $type: bpmn:Task, id: Task_0l942o9, name: report delay, $parent: Process_0hiditg }
- { $type: bpmn:IntermediateCatchEvent, id: IntermediateCatchEvent_0yg7cuh, name: credit score received, eventDefinitions: [object Object], $parent: Process_0hiditg }
- { $type: bpmn:IntermediateCatchEvent, id: IntermediateCatchEvent_0yg7cuh, name: credit score received, eventDefinitions: [object Object], $parent: Process_0hiditg }
- { $type: bpmn:IntermediateCatchEvent, id: IntermediateCatchEvent_0a8iz14, name: credit score received, eventDefinitions: [object Object], $parent: Process_0hiditg }
- { $type: bpmn:IntermediateCatchEvent, id: IntermediateCatchEvent_0a8iz14, name: credit score received, eventDefinitions: [object Object], $parent: Process_0hiditg }
- { $type: bpmn:StartEvent, id: StartEvent_1els7eb, name: scoring request received, eventDefinitions: [object Object], $parent: Process_0hiditg }
- { $type: bpmn:StartEvent, id: StartEvent_1els7eb, name: scoring request received, eventDefinitions: [object Object], $parent: Process_0hiditg }
- { $type: bpmn:IntermediateCatchEvent, id: IntermediateCatchEvent_0ujob24, name: delay information received, eventDefinitions: [object Object], $parent: Process_0hiditg }
- { $type: bpmn:IntermediateCatchEvent, id: IntermediateCatchEvent_0ujob24, name: delay information received, eventDefinitions: [object Object], $parent: Process_0hiditg }
- { $type: bpmn:EventBasedGateway, id: EventBasedGateway_02s95tm, $parent: Process_0hiditg }
- { $type: bpmn:Participant, id: Participant_1xfb3ml, name: scoring service, processRef: Process_1dc1p3b, $parent: Collaboration_1y0blh3 }
- { $type: bpmn:Task, id: Task_07vbn2i, name: send credit score, $parent: Process_1dc1p3b }
- { $type: bpmn:Task, id: Task_01ouvha, name: report delay, $parent: Process_1dc1p3b }
- { $type: bpmn:ExclusiveGateway, id: ExclusiveGateway_0rtdod4, name: score available?, $parent: Process_1dc1p3b }
- { $type: bpmn:ExclusiveGateway, id: ExclusiveGateway_0rtdod4, name: score available?, $parent: Process_1dc1p3b }
- { $type: bpmn:Task, id: Task_06dqs9t, name: send credit score, $parent: Process_1dc1p3b }
- { $type: bpmn:EndEvent, id: EndEvent_0khk0tq, name: scoring request handled, eventDefinitions: , $parent: Process_1dc1p3b }
- { $type: bpmn:EndEvent, id: EndEvent_0khk0tq, name: scoring request handled, eventDefinitions: , $parent: Process_1dc1p3b }
- { $type: bpmn:ExclusiveGateway, id: ExclusiveGateway_125lzox, $parent: Process_1dc1p3b }
- { $type: bpmn:Task, id: Task_02m68xj, name: compute credit score (level 2), $parent: Process_1dc1p3b }
- { $type: bpmn:Task, id: Task_1r15hqs, name: compute credit score (level 1), $parent: Process_1dc1p3b }
- { $type: bpmn:StartEvent, id: StartEvent_0o849un, name: scoring request received, eventDefinitions: [object Object], $parent: Process_1dc1p3b }
- { $type: bpmn:StartEvent, id: StartEvent_0o849un, name: scoring request received, eventDefinitions: [object Object], $parent: Process_1dc1p3b }
- { $type: bpmn:TextAnnotation, id: TextAnnotation_0si9ilm, text: inkl. ID for message\nqueueing, $parent: Process_1dc1p3b }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_0rrtx7k, sourceRef: StartEvent_1els7eb, targetRef: Task_16winvj, $parent: Process_0hiditg }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_1i1amgb, sourceRef: IntermediateCatchEvent_0a8iz14, targetRef: ExclusiveGateway_11dldcm, $parent: Process_0hiditg }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_1fy80l7, sourceRef: IntermediateCatchEvent_0yg7cuh, targetRef: ExclusiveGateway_11dldcm, $parent: Process_0hiditg }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_12a77en, sourceRef: ExclusiveGateway_11dldcm, targetRef: Task_1fzfxey, $parent: Process_0hiditg }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_1nyeozm, sourceRef: Task_1fzfxey, targetRef: EndEvent_0rp5trg, $parent: Process_0hiditg }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_0rf5cxd, sourceRef: IntermediateCatchEvent_0ujob24, targetRef: Task_0l942o9, $parent: Process_0hiditg }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_08fsgff, sourceRef: Task_0l942o9, targetRef: IntermediateCatchEvent_0a8iz14, $parent: Process_0hiditg }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_0o5t8lw, sourceRef: Task_16winvj, targetRef: EventBasedGateway_02s95tm, $parent: Process_0hiditg }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_0e97dad, sourceRef: EventBasedGateway_02s95tm, targetRef: IntermediateCatchEvent_0ujob24, $parent: Process_0hiditg }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_1kdut76, sourceRef: EventBasedGateway_02s95tm, targetRef: IntermediateCatchEvent_0yg7cuh, $parent: Process_0hiditg }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_0jh32vv, name: no, sourceRef: ExclusiveGateway_0rtdod4, targetRef: Task_01ouvha, $parent: Process_1dc1p3b }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_0jh32vv, name: no, sourceRef: ExclusiveGateway_0rtdod4, targetRef: Task_01ouvha, $parent: Process_1dc1p3b }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_052bcer, name: yes, sourceRef: ExclusiveGateway_0rtdod4, targetRef: Task_07vbn2i, $parent: Process_1dc1p3b }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_052bcer, name: yes, sourceRef: ExclusiveGateway_0rtdod4, targetRef: Task_07vbn2i, $parent: Process_1dc1p3b }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_0t0wbx3, sourceRef: ExclusiveGateway_125lzox, targetRef: EndEvent_0khk0tq, $parent: Process_1dc1p3b }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_0dkbeo7, sourceRef: Task_06dqs9t, targetRef: ExclusiveGateway_125lzox, $parent: Process_1dc1p3b }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_1xqy47o, sourceRef: Task_07vbn2i, targetRef: ExclusiveGateway_125lzox, $parent: Process_1dc1p3b }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_08jl5se, sourceRef: Task_02m68xj, targetRef: Task_06dqs9t, $parent: Process_1dc1p3b }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_1yiajt6, sourceRef: Task_01ouvha, targetRef: Task_02m68xj, $parent: Process_1dc1p3b }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_1nznlgx, sourceRef: Task_1r15hqs, targetRef: ExclusiveGateway_0rtdod4, $parent: Process_1dc1p3b }
- { $type: bpmn:SequenceFlow, id: SequenceFlow_158pur5, sourceRef: StartEvent_0o849un, targetRef: Task_1r15hqs, $parent: Process_1dc1p3b }
- { $type: bpmn:Association, id: Association_1ctd4ma, sourceRef: Task_01ouvha, targetRef: TextAnnotation_0si9ilm, $parent: Process_1dc1p3b }
- { $type: bpmn:MessageFlow, id: MessageFlow_1pkfls0, sourceRef: Participant_1x9zkso, targetRef: StartEvent_1els7eb, $parent: Collaboration_1y0blh3 }
- { $type: bpmn:MessageFlow, id: MessageFlow_1m6362g, sourceRef: Task_0l942o9, targetRef: Participant_1x9zkso, $parent: Collaboration_1y0blh3 }
- { $type: bpmn:MessageFlow, id: MessageFlow_1i21wes, sourceRef: Task_1fzfxey, targetRef: Participant_1x9zkso, $parent: Collaboration_1y0blh3 }
- { $type: bpmn:MessageFlow, id: MessageFlow_1mm30jd, sourceRef: Task_16winvj, targetRef: StartEvent_0o849un, $parent: Collaboration_1y0blh3 }
- { $type: bpmn:MessageFlow, id: MessageFlow_1136yi9, sourceRef: Task_07vbn2i, targetRef: IntermediateCatchEvent_0yg7cuh, $parent: Collaboration_1y0blh3 }
- { $type: bpmn:MessageFlow, id: MessageFlow_0bgkr12, sourceRef: Task_06dqs9t, targetRef: IntermediateCatchEvent_0a8iz14, $parent: Collaboration_1y0blh3 }
- { $type: bpmn:MessageFlow, id: MessageFlow_1nwyn8k, sourceRef: Task_01ouvha, targetRef: IntermediateCatchEvent_0ujob24, $parent: Collaboration_1y0blh3 }\n"""

process_textual_representation_simplified_xml = """<definitions Definitions_1>\n    <collaboration Collaboration_1y0blh3>\n        <participant Participant_1x9zkso> (credit scoring frontend (bank))\n          - processRef: Process_1\n
  </participant>\n        <participant Participant_0e81yis> (credit scoring (bank))\n          - processRef: Process_0hiditg\n        </participant>\n        <participant Participant_1xfb3ml> (scoring service)\n          - processRef: Process_1dc1p3b\n        </participant>\n        <messageFlow MessageFlow_1pkfls0>\n          - sourceRef: Participant_1x9zkso\n
   - targetRef: StartEvent_1els7eb\n        </messageFlow>\n        <messageFlow MessageFlow_1m6362g>\n          - sourceRef: Task_0l942o9\n          - targetRef: Participant_1x9zkso\n
       </messageFlow>\n        <messageFlow MessageFlow_1i21wes>\n          - sourceRef: Task_1fzfxey\n          - targetRef: Participant_1x9zkso\n        </messageFlow>\n        <messageFlow MessageFlow_1mm30jd>\n          - sourceRef: Task_16winvj\n          - targetRef: StartEvent_0o849un\n        </messageFlow>\n        <messageFlow MessageFlow_1136yi9>\n
 - sourceRef: Task_07vbn2i\n          - targetRef: IntermediateCatchEvent_0yg7cuh\n        </messageFlow>\n        <messageFlow MessageFlow_0bgkr12>\n          - sourceRef: Task_06dqs9t\n          - targetRef: IntermediateCatchEvent_0a8iz14\n        </messageFlow>\n        <messageFlow MessageFlow_1nwyn8k>\n          - sourceRef: Task_01ouvha\n          - targetRef: IntermediateCatchEvent_0ujob24\n        </messageFlow>\n    </collaboration>\n    <process Process_1>\n      - isExecutable: false\n    </process>\n    <process Process_0hiditg>\n
 <task Task_16winvj (request credit score)/>\n        <exclusiveGateway ExclusiveGateway_11dldcm/>\n        <task Task_1fzfxey (send credit score)/>\n        <endEvent EndEvent_0rp5trg
(scoring request handled)/>\n        <task Task_0l942o9 (report delay)/>\n        <sequenceFlow SequenceFlow_0rrtx7k>\n          - sourceRef: StartEvent_1els7eb\n          - targetRef:
Task_16winvj\n        </sequenceFlow>\n        <sequenceFlow SequenceFlow_1i1amgb>\n          - sourceRef: IntermediateCatchEvent_0a8iz14\n          - targetRef: ExclusiveGateway_11dldcm\n        </sequenceFlow>\n        <sequenceFlow SequenceFlow_1fy80l7>\n          - sourceRef: IntermediateCatchEvent_0yg7cuh\n          - targetRef: ExclusiveGateway_11dldcm\n
</sequenceFlow>\n        <sequenceFlow SequenceFlow_12a77en>\n          - sourceRef: ExclusiveGateway_11dldcm\n          - targetRef: Task_1fzfxey\n        </sequenceFlow>\n        <sequenceFlow SequenceFlow_1nyeozm>\n          - sourceRef: Task_1fzfxey\n          - targetRef: EndEvent_0rp5trg\n        </sequenceFlow>\n        <sequenceFlow SequenceFlow_0rf5cxd>\n
      - sourceRef: IntermediateCatchEvent_0ujob24\n          - targetRef: Task_0l942o9\n        </sequenceFlow>\n        <sequenceFlow SequenceFlow_08fsgff>\n          - sourceRef: Task_0l942o9\n          - targetRef: IntermediateCatchEvent_0a8iz14\n        </sequenceFlow>\n        <intermediateCatchEvent IntermediateCatchEvent_0yg7cuh> (credit score received)\n
      <messageEventDefinition/>\n        </intermediateCatchEvent>\n        <intermediateCatchEvent IntermediateCatchEvent_0a8iz14> (credit score received)\n            <messageEventDefinition/>\n        </intermediateCatchEvent>\n        <startEvent StartEvent_1els7eb> (scoring request received)\n            <messageEventDefinition/>\n        </startEvent>\n        <intermediateCatchEvent IntermediateCatchEvent_0ujob24> (delay information received)\n            <messageEventDefinition/>\n        </intermediateCatchEvent>\n        <sequenceFlow SequenceFlow_0o5t8lw>\n          - sourceRef: Task_16winvj\n          - targetRef: EventBasedGateway_02s95tm\n        </sequenceFlow>\n        <eventBasedGateway EventBasedGateway_02s95tm/>\n        <sequenceFlow SequenceFlow_0e97dad>\n          - sourceRef: EventBasedGateway_02s95tm\n          - targetRef: IntermediateCatchEvent_0ujob24\n        </sequenceFlow>\n
<sequenceFlow SequenceFlow_1kdut76>\n          - sourceRef: EventBasedGateway_02s95tm\n          - targetRef: IntermediateCatchEvent_0yg7cuh\n        </sequenceFlow>\n    </process>\n
  <process Process_1dc1p3b>\n        <sequenceFlow SequenceFlow_0jh32vv> (no)\n          - sourceRef: ExclusiveGateway_0rtdod4\n          - targetRef: Task_01ouvha\n        </sequenceFlow>\n        <sequenceFlow SequenceFlow_052bcer> (yes)\n          - sourceRef: ExclusiveGateway_0rtdod4\n          - targetRef: Task_07vbn2i\n        </sequenceFlow>\n        <sequenceFlow SequenceFlow_0t0wbx3>\n          - sourceRef: ExclusiveGateway_125lzox\n          - targetRef: EndEvent_0khk0tq\n        </sequenceFlow>\n        <sequenceFlow SequenceFlow_0dkbeo7>\n          - sourceRef: Task_06dqs9t\n          - targetRef: ExclusiveGateway_125lzox\n        </sequenceFlow>\n        <sequenceFlow SequenceFlow_1xqy47o>\n          - sourceRef: Task_07vbn2i\n          - targetRef: ExclusiveGateway_125lzox\n        </sequenceFlow>\n        <sequenceFlow SequenceFlow_08jl5se>\n          - sourceRef: Task_02m68xj\n          - targetRef: Task_06dqs9t\n        </sequenceFlow>\n        <sequenceFlow SequenceFlow_1yiajt6>\n          - sourceRef: Task_01ouvha\n          - targetRef: Task_02m68xj\n        </sequenceFlow>\n        <sequenceFlow SequenceFlow_1nznlgx>\n          - sourceRef: Task_1r15hqs\n          - targetRef: ExclusiveGateway_0rtdod4\n        </sequenceFlow>\n        <sequenceFlow SequenceFlow_158pur5>\n          - sourceRef: StartEvent_0o849un\n          - targetRef: Task_1r15hqs\n        </sequenceFlow>\n        <task Task_07vbn2i (send credit score)/>\n        <task Task_01ouvha (report delay)/>\n        <exclusiveGateway ExclusiveGateway_0rtdod4 (score available?)/>\n        <task Task_06dqs9t (send credit score)/>\n        <endEvent EndEvent_0khk0tq (scoring request handled)/>\n        <exclusiveGateway ExclusiveGateway_125lzox/>\n        <task Task_02m68xj (compute credit score (level 2))/>\n        <task Task_1r15hqs (compute credit score (level 1))/>\n        <startEvent StartEvent_0o849un> (scoring request received)\n            <messageEventDefinition/>\n        </startEvent>\n        <association Association_1ctd4ma>\n          - sourceRef: Task_01ouvha\n          - targetRef: TextAnnotation_0si9ilm\n        </association>\n        <textAnnotation TextAnnotation_0si9ilm>\n
  <text (inkl. ID for message queueing)/>\n        </textAnnotation>\n    </process>\n</definitions>\n"""

examples_json = [
    {
        "input": "How does the bank start the credit scoring process?",
        "output_good": "A bank clerk uses their software to request a credit score for a customer, which kicks off the process in the banking system to communicate with the credit protection agency.",
        "output_bad": "The bank initiates a BPMN Collaboration, invoking a Participant Process via a MessageFlow to the Schufa service for a credit scoring Event.",
    },
    {
        "input": "What happens after the bank sends a scoring request to the agency?",
        "output_good": "The agency performs an initial credit scoring, and if this initial scoring is successful, the result is sent back immediately to the bank's system and shown to the clerk.",
        "output_bad": "Upon receipt of the scoring request, an IntermediateCatchEvent is triggered, leading to an immediate execution of a Task for level 1 scoring, conditioned by an ExclusiveGateway.",
    },
    {
        "input": "What occurs if the initial credit scoring doesn’t give an immediate result?",
        "output_good": "The agency informs the bank's system about the delay and starts a more detailed scoring. The bank's system then sends a notification to the clerk to report the delay.",
        "output_bad": "If the initial scoring doesn't resolve, a conditional ExclusiveGateway routes the flow to a delay notification Task, subsequently initializing a level 2 scoring Sub-Process.",
    },
    {
        "input": "How is the clerk informed of the final credit scoring result?",
        "output_good": "Once the scoring is completed and the result is sent back to the bank's system, it is sent to the clerk's software.",
        "output_bad": "The final scoring outcome, after processing through a sequence of EventBasedGateways and Task executions, is programmatically dispatched to the initiating Participant's frontend interface.",
    },
    {
        "input": "What does the bank do if the credit score is delayed?",
        "output_good": "The bank's system sends a notification to the clerk to report the delay, and as soon as the final score is ready, it sends the results to the clerk.",
        "output_bad": "In the event of a scoring delay, an IntermediateCatchEvent captures the timeout, activating a Task to update the UI component of the clerk's software module with a delay notification.",
    },
]


def few_shots_learning_json(abstraction):
    res = "- Let us consider the following textual representation of an example process:\n"
    res += abstraction + "\n\n"
    res += "- These are example pairs of input and expected output:\n"
    for i in range(len(examples_json)):
        res += f"Input {i}: {examples_json[i]['input']}\n"
        res += f"Expected output {i}: {examples_json[i]['output_good']}\n"
    res += "\n\n"
    return res


def negative_prompting_json():
    res = "- Now, I will give you example bad outputs for the same example questions, so you try to avoid such outputs:\n"
    for i in range(len(examples_json)):
        res += f"Bad output for question {i}: {examples_json[i]['output_bad']}\n"
    res += "\n\n"
    return res


def negative_prompting_with_questions(abstraction):
    res = "- Let us consider the following textual representation of an example process:\n"
    res += abstraction + "\n\n"
    res = "- Now, I will give you example pairs of input questions and bad outputs that you should try to avoid:\n"
    for i in range(len(examples_json)):
        res += f"Input {i}: {examples_json[i]['input']}\n"
        res += f"Bad output for question {i}: {examples_json[i]['output_bad']}\n"
    res += "\n\n"
    return res


def get_examples():
    res = (
        "- Now, I will give you example triples of input questions, good answers,"
        " and bad answers that you should try to avoid:\n"
    )
    for i in range(len(examples_json)):
        res += f"Input {i}: {examples_json[i]['input']}\n"
        res += f"Good answer for question {i}: {examples_json[i]['output_good']}\n"
        res += f"Bad answer for question {i}: {examples_json[i]['output_bad']}\n"
    res += "\n\n"
    return res
