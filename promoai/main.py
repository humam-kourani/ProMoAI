
from pm4py import discover_powl, BPMN, convert_to_petri_net, PetriNet
from promoai.model_generation.llm_model_generator import LLMProcessModelGenerator
from aipa.bpmn_analyzer import BPMNAnalyzer




from promoai.pn_to_powl.converter import convert_workflow_net_to_powl
from pm4py.algo.discovery.powl.inductive.variants.powl_discovery_varaints import POWLDiscoveryVariant


def generate_model_from_text(description:str, api_key:str, ai_model:str, ai_provider:str):
    return LLMProcessModelGenerator.from_description(description, api_key, ai_model, ai_provider)


def generate_model_from_event_log(event_log):
    powl_model = discover_powl(event_log, variant=POWLDiscoveryVariant.MAXIMAL)
    return LLMProcessModelGenerator.from_powl(powl_model=powl_model)


def generate_model_from_petri_net(pn: PetriNet):
    powl_model = convert_workflow_net_to_powl(pn)
    return LLMProcessModelGenerator.from_powl(powl_model=powl_model)


def generate_model_from_bpmn(bpmn_diagram:BPMN):
    pn, im, fm = convert_to_petri_net(bpmn_diagram)
    return generate_model_from_petri_net(pn)

def generate_response_from_bpmn(bpmn_xml_string: str, query: str, api_key:str, ai_model:str, ai_provider:str):
    return BPMNAnalyzer(bpmn_xml_string, query, api_key, ai_model, ai_provider).generate_response()


if __name__ == "__main__":
    bpmn_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
    <bpmn:collaboration id="Collaboration_0geryc1">
        <bpmn:participant id="Participant_0ygkg4f" name="Dispatch of goods&#10;Computer Hardware Shop" processRef="Process_1" />
    </bpmn:collaboration>
    <bpmn:process id="Process_1" isExecutable="false">
        <bpmn:laneSet>
        <bpmn:lane id="Lane_1viot5w" name="Logistics">
            <bpmn:flowNodeRef>Task_12j0pib</bpmn:flowNodeRef>
        </bpmn:lane>
        <bpmn:lane id="Lane_1ocseyo" name="Secretary">
            <bpmn:flowNodeRef>Task_0jsoxba</bpmn:flowNodeRef>
            <bpmn:flowNodeRef>Task_0vaxgaa</bpmn:flowNodeRef>
            <bpmn:flowNodeRef>Task_0e6hvnj</bpmn:flowNodeRef>
            <bpmn:flowNodeRef>Task_0s79ile</bpmn:flowNodeRef>
            <bpmn:flowNodeRef>InclusiveGateway_0p2e5vq</bpmn:flowNodeRef>
            <bpmn:flowNodeRef>InclusiveGateway_1dgb4sg</bpmn:flowNodeRef>
            <bpmn:flowNodeRef>StartEvent_1</bpmn:flowNodeRef>
            <bpmn:flowNodeRef>ParallelGateway_02fgrfq</bpmn:flowNodeRef>
            <bpmn:flowNodeRef>ExclusiveGateway_1mpgzhg</bpmn:flowNodeRef>
            <bpmn:flowNodeRef>ExclusiveGateway_1ouv9kf</bpmn:flowNodeRef>
        </bpmn:lane>
        <bpmn:lane id="Lane_1vl2igx" name="Warehouse">
            <bpmn:flowNodeRef>Task_05ftug5</bpmn:flowNodeRef>
            <bpmn:flowNodeRef>Task_0sl26uo</bpmn:flowNodeRef>
            <bpmn:flowNodeRef>ExclusiveGateway_0z5sib0</bpmn:flowNodeRef>
            <bpmn:flowNodeRef>EndEvent_1fx9yp3</bpmn:flowNodeRef>
        </bpmn:lane>
        </bpmn:laneSet>
        <bpmn:sequenceFlow id="SequenceFlow_0iu9po7" name="no" sourceRef="ExclusiveGateway_1mpgzhg" targetRef="InclusiveGateway_0p2e5vq" />
        <bpmn:inclusiveGateway id="InclusiveGateway_0p2e5vq">
        <bpmn:incoming>SequenceFlow_0iu9po7</bpmn:incoming>
        <bpmn:outgoing>SequenceFlow_1j94oja</bpmn:outgoing>
        <bpmn:outgoing>SequenceFlow_1dlbln9</bpmn:outgoing>
        </bpmn:inclusiveGateway>
        <bpmn:task id="Task_12j0pib" name="Insure parcel">
        <bpmn:incoming>SequenceFlow_1j94oja</bpmn:incoming>
        <bpmn:outgoing>SequenceFlow_0kz5g1t</bpmn:outgoing>
        </bpmn:task>
        <bpmn:sequenceFlow id="SequenceFlow_1j94oja" name="If insurance&#10;necessary" sourceRef="InclusiveGateway_0p2e5vq" targetRef="Task_12j0pib" />
        <bpmn:task id="Task_0jsoxba" name="Write package&#10;label">
        <bpmn:incoming>SequenceFlow_1dlbln9</bpmn:incoming>
        <bpmn:outgoing>SequenceFlow_0mp5byl</bpmn:outgoing>
        </bpmn:task>
        <bpmn:sequenceFlow id="SequenceFlow_1dlbln9" name="always" sourceRef="InclusiveGateway_0p2e5vq" targetRef="Task_0jsoxba" />
        <bpmn:sequenceFlow id="SequenceFlow_0mp5byl" sourceRef="Task_0jsoxba" targetRef="InclusiveGateway_1dgb4sg" />
        <bpmn:inclusiveGateway id="InclusiveGateway_1dgb4sg">
        <bpmn:incoming>SequenceFlow_0mp5byl</bpmn:incoming>
        <bpmn:incoming>SequenceFlow_0kz5g1t</bpmn:incoming>
        <bpmn:outgoing>SequenceFlow_0buzwss</bpmn:outgoing>
        </bpmn:inclusiveGateway>
        <bpmn:sequenceFlow id="SequenceFlow_0kz5g1t" sourceRef="Task_12j0pib" targetRef="InclusiveGateway_1dgb4sg" />
        <bpmn:startEvent id="StartEvent_1" name="Ship goods">
        <bpmn:outgoing>SequenceFlow_14a0oky</bpmn:outgoing>
        </bpmn:startEvent>
        <bpmn:parallelGateway id="ParallelGateway_02fgrfq">
        <bpmn:incoming>SequenceFlow_14a0oky</bpmn:incoming>
        <bpmn:outgoing>SequenceFlow_023hzxi</bpmn:outgoing>
        <bpmn:outgoing>SequenceFlow_1ujhfx4</bpmn:outgoing>
        </bpmn:parallelGateway>
        <bpmn:task id="Task_0vaxgaa" name="Clarify shipment method">
        <bpmn:incoming>SequenceFlow_023hzxi</bpmn:incoming>
        <bpmn:outgoing>SequenceFlow_1rss71o</bpmn:outgoing>
        </bpmn:task>
        <bpmn:exclusiveGateway id="ExclusiveGateway_1mpgzhg" name="Special&#10;sandling?">
        <bpmn:incoming>SequenceFlow_1rss71o</bpmn:incoming>
        <bpmn:outgoing>SequenceFlow_0iu9po7</bpmn:outgoing>
        <bpmn:outgoing>SequenceFlow_1xv6wk4</bpmn:outgoing>
        </bpmn:exclusiveGateway>
        <bpmn:sequenceFlow id="SequenceFlow_14a0oky" sourceRef="StartEvent_1" targetRef="ParallelGateway_02fgrfq" />
        <bpmn:sequenceFlow id="SequenceFlow_023hzxi" sourceRef="ParallelGateway_02fgrfq" targetRef="Task_0vaxgaa" />
        <bpmn:sequenceFlow id="SequenceFlow_1rss71o" sourceRef="Task_0vaxgaa" targetRef="ExclusiveGateway_1mpgzhg" />
        <bpmn:task id="Task_0e6hvnj" name="Get 3 offers&#10;from logistic&#10;companies">
        <bpmn:incoming>SequenceFlow_1xv6wk4</bpmn:incoming>
        <bpmn:outgoing>SequenceFlow_1pq8ub3</bpmn:outgoing>
        </bpmn:task>
        <bpmn:sequenceFlow id="SequenceFlow_1xv6wk4" name="yes" sourceRef="ExclusiveGateway_1mpgzhg" targetRef="Task_0e6hvnj" />
        <bpmn:task id="Task_0s79ile" name="Select logistic&#10;company and&#10;place order">
        <bpmn:incoming>SequenceFlow_1pq8ub3</bpmn:incoming>
        <bpmn:outgoing>SequenceFlow_0ajhekx</bpmn:outgoing>
        </bpmn:task>
        <bpmn:sequenceFlow id="SequenceFlow_1pq8ub3" sourceRef="Task_0e6hvnj" targetRef="Task_0s79ile" />
        <bpmn:exclusiveGateway id="ExclusiveGateway_1ouv9kf">
        <bpmn:incoming>SequenceFlow_0ajhekx</bpmn:incoming>
        <bpmn:incoming>SequenceFlow_0buzwss</bpmn:incoming>
        <bpmn:outgoing>SequenceFlow_035vf60</bpmn:outgoing>
        </bpmn:exclusiveGateway>
        <bpmn:sequenceFlow id="SequenceFlow_0ajhekx" sourceRef="Task_0s79ile" targetRef="ExclusiveGateway_1ouv9kf" />
        <bpmn:sequenceFlow id="SequenceFlow_0buzwss" sourceRef="InclusiveGateway_1dgb4sg" targetRef="ExclusiveGateway_1ouv9kf" />
        <bpmn:task id="Task_05ftug5" name="Package goods">
        <bpmn:incoming>SequenceFlow_1ujhfx4</bpmn:incoming>
        <bpmn:outgoing>SequenceFlow_0b2nw5c</bpmn:outgoing>
        </bpmn:task>
        <bpmn:exclusiveGateway id="ExclusiveGateway_0z5sib0">
        <bpmn:incoming>SequenceFlow_035vf60</bpmn:incoming>
        <bpmn:incoming>SequenceFlow_0b2nw5c</bpmn:incoming>
        <bpmn:outgoing>SequenceFlow_06kfaev</bpmn:outgoing>
        </bpmn:exclusiveGateway>
        <bpmn:sequenceFlow id="SequenceFlow_035vf60" sourceRef="ExclusiveGateway_1ouv9kf" targetRef="ExclusiveGateway_0z5sib0" />
        <bpmn:sequenceFlow id="SequenceFlow_0b2nw5c" sourceRef="Task_05ftug5" targetRef="ExclusiveGateway_0z5sib0" />
        <bpmn:task id="Task_0sl26uo" name="Prepare for&#10;picking up&#10;goods">
        <bpmn:incoming>SequenceFlow_06kfaev</bpmn:incoming>
        <bpmn:outgoing>SequenceFlow_0v64x8b</bpmn:outgoing>
        </bpmn:task>
        <bpmn:sequenceFlow id="SequenceFlow_06kfaev" sourceRef="ExclusiveGateway_0z5sib0" targetRef="Task_0sl26uo" />
        <bpmn:endEvent id="EndEvent_1fx9yp3" name="Shipment&#10;prepared">
        <bpmn:incoming>SequenceFlow_0v64x8b</bpmn:incoming>
        </bpmn:endEvent>
        <bpmn:sequenceFlow id="SequenceFlow_0v64x8b" sourceRef="Task_0sl26uo" targetRef="EndEvent_1fx9yp3" />
        <bpmn:sequenceFlow id="SequenceFlow_1ujhfx4" sourceRef="ParallelGateway_02fgrfq" targetRef="Task_05ftug5" />
    </bpmn:process>
    <bpmndi:BPMNDiagram id="BPMNDiagram_1">
        <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Collaboration_0geryc1">
        <bpmndi:BPMNShape id="Participant_0ygkg4f_di" bpmnElement="Participant_0ygkg4f">
            <dc:Bounds x="252" y="88" width="1260" height="752" />
        </bpmndi:BPMNShape>
        <bpmndi:BPMNShape id="_BPMNShape_StartEvent_2" bpmnElement="StartEvent_1">
            <dc:Bounds x="329" y="466" width="36" height="36" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="302" y="502" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNShape>
        <bpmndi:BPMNShape id="Lane_1viot5w_di" bpmnElement="Lane_1viot5w">
            <dc:Bounds x="282" y="88" width="1230" height="216" />
        </bpmndi:BPMNShape>
        <bpmndi:BPMNShape id="Lane_1ocseyo_di" bpmnElement="Lane_1ocseyo">
            <dc:Bounds x="282" y="304" width="1230" height="291" />
        </bpmndi:BPMNShape>
        <bpmndi:BPMNShape id="Lane_1vl2igx_di" bpmnElement="Lane_1vl2igx">
            <dc:Bounds x="282" y="595" width="1230" height="245" />
        </bpmndi:BPMNShape>
        <bpmndi:BPMNEdge id="SequenceFlow_14a0oky_di" bpmnElement="SequenceFlow_14a0oky">
            <di:waypoint xsi:type="dc:Point" x="365" y="484" />
            <di:waypoint xsi:type="dc:Point" x="407" y="484" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="341" y="474" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNShape id="ParallelGateway_02fgrfq_di" bpmnElement="ParallelGateway_02fgrfq">
            <dc:Bounds x="407" y="459" width="50" height="50" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="387" y="509" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNShape>
        <bpmndi:BPMNShape id="Task_0vaxgaa_di" bpmnElement="Task_0vaxgaa">
            <dc:Bounds x="490" y="444" width="100" height="80" />
        </bpmndi:BPMNShape>
        <bpmndi:BPMNEdge id="SequenceFlow_023hzxi_di" bpmnElement="SequenceFlow_023hzxi">
            <di:waypoint xsi:type="dc:Point" x="457" y="484" />
            <di:waypoint xsi:type="dc:Point" x="490" y="484" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="428.5" y="474" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNShape id="ExclusiveGateway_1mpgzhg_di" bpmnElement="ExclusiveGateway_1mpgzhg" isMarkerVisible="true">
            <dc:Bounds x="628" y="459" width="50" height="50" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="608" y="509" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNShape>
        <bpmndi:BPMNEdge id="SequenceFlow_1rss71o_di" bpmnElement="SequenceFlow_1rss71o">
            <di:waypoint xsi:type="dc:Point" x="590" y="484" />
            <di:waypoint xsi:type="dc:Point" x="628" y="484" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="564" y="474" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNEdge id="SequenceFlow_0iu9po7_di" bpmnElement="SequenceFlow_0iu9po7">
            <di:waypoint xsi:type="dc:Point" x="653" y="459" />
            <di:waypoint xsi:type="dc:Point" x="653" y="375" />
            <di:waypoint xsi:type="dc:Point" x="698" y="375" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="620" y="433.5" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNShape id="InclusiveGateway_0p2e5vq_di" bpmnElement="InclusiveGateway_0p2e5vq">
            <dc:Bounds x="698" y="350" width="50" height="50" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="678" y="400" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNShape>
        <bpmndi:BPMNShape id="Task_12j0pib_di" bpmnElement="Task_12j0pib">
            <dc:Bounds x="781" y="163" width="100" height="80" />
        </bpmndi:BPMNShape>
        <bpmndi:BPMNEdge id="SequenceFlow_1j94oja_di" bpmnElement="SequenceFlow_1j94oja">
            <di:waypoint xsi:type="dc:Point" x="723" y="350" />
            <di:waypoint xsi:type="dc:Point" x="723" y="203" />
            <di:waypoint xsi:type="dc:Point" x="781" y="203" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="678" y="317.5" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNShape id="Task_0jsoxba_di" bpmnElement="Task_0jsoxba">
            <dc:Bounds x="781" y="335" width="100" height="80" />
        </bpmndi:BPMNShape>
        <bpmndi:BPMNEdge id="SequenceFlow_1dlbln9_di" bpmnElement="SequenceFlow_1dlbln9">
            <di:waypoint xsi:type="dc:Point" x="748" y="375" />
            <di:waypoint xsi:type="dc:Point" x="781" y="375" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="719.5" y="374" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNEdge id="SequenceFlow_0mp5byl_di" bpmnElement="SequenceFlow_0mp5byl">
            <di:waypoint xsi:type="dc:Point" x="881" y="375" />
            <di:waypoint xsi:type="dc:Point" x="936" y="375" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="863.5" y="365" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNShape id="InclusiveGateway_1dgb4sg_di" bpmnElement="InclusiveGateway_1dgb4sg">
            <dc:Bounds x="936" y="350" width="50" height="50" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="916" y="400" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNShape>
        <bpmndi:BPMNEdge id="SequenceFlow_0kz5g1t_di" bpmnElement="SequenceFlow_0kz5g1t">
            <di:waypoint xsi:type="dc:Point" x="881" y="203" />
            <di:waypoint xsi:type="dc:Point" x="961" y="203" />
            <di:waypoint xsi:type="dc:Point" x="961" y="350" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="876" y="193" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNShape id="Task_0e6hvnj_di" bpmnElement="Task_0e6hvnj">
            <dc:Bounds x="705" y="444" width="100" height="80" />
        </bpmndi:BPMNShape>
        <bpmndi:BPMNEdge id="SequenceFlow_1xv6wk4_di" bpmnElement="SequenceFlow_1xv6wk4">
            <di:waypoint xsi:type="dc:Point" x="678" y="484" />
            <di:waypoint xsi:type="dc:Point" x="705" y="484" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="646.5" y="483" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNShape id="Task_0s79ile_di" bpmnElement="Task_0s79ile">
            <dc:Bounds x="861" y="444" width="100" height="80" />
        </bpmndi:BPMNShape>
        <bpmndi:BPMNEdge id="SequenceFlow_1pq8ub3_di" bpmnElement="SequenceFlow_1pq8ub3">
            <di:waypoint xsi:type="dc:Point" x="805" y="484" />
            <di:waypoint xsi:type="dc:Point" x="861" y="484" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="788" y="474" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNShape id="ExclusiveGateway_1ouv9kf_di" bpmnElement="ExclusiveGateway_1ouv9kf" isMarkerVisible="true">
            <dc:Bounds x="1032" y="459" width="50" height="50" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="1012" y="509" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNShape>
        <bpmndi:BPMNEdge id="SequenceFlow_0ajhekx_di" bpmnElement="SequenceFlow_0ajhekx">
            <di:waypoint xsi:type="dc:Point" x="961" y="484" />
            <di:waypoint xsi:type="dc:Point" x="1032" y="484" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="951.5" y="474" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNEdge id="SequenceFlow_0buzwss_di" bpmnElement="SequenceFlow_0buzwss">
            <di:waypoint xsi:type="dc:Point" x="986" y="375" />
            <di:waypoint xsi:type="dc:Point" x="1057" y="375" />
            <di:waypoint xsi:type="dc:Point" x="1057" y="459" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="916" y="432" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNShape id="Task_05ftug5_di" bpmnElement="Task_05ftug5">
            <dc:Bounds x="490" y="666.8154402895054" width="100" height="80" />
        </bpmndi:BPMNShape>
        <bpmndi:BPMNShape id="ExclusiveGateway_0z5sib0_di" bpmnElement="ExclusiveGateway_0z5sib0" isMarkerVisible="true">
            <dc:Bounds x="1153.2062726176116" y="682" width="50" height="50" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="1133.2062726176116" y="732" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNShape>
        <bpmndi:BPMNEdge id="SequenceFlow_035vf60_di" bpmnElement="SequenceFlow_035vf60">
            <di:waypoint xsi:type="dc:Point" x="1082" y="484" />
            <di:waypoint xsi:type="dc:Point" x="1178" y="484" />
            <di:waypoint xsi:type="dc:Point" x="1178" y="682" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="1012" y="598" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNEdge id="SequenceFlow_0b2nw5c_di" bpmnElement="SequenceFlow_0b2nw5c">
            <di:waypoint xsi:type="dc:Point" x="590" y="707" />
            <di:waypoint xsi:type="dc:Point" x="1153" y="707" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="826.5" y="697" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNShape id="Task_0sl26uo_di" bpmnElement="Task_0sl26uo">
            <dc:Bounds x="1254.2062726176116" y="667" width="100" height="80" />
        </bpmndi:BPMNShape>
        <bpmndi:BPMNEdge id="SequenceFlow_06kfaev_di" bpmnElement="SequenceFlow_06kfaev">
            <di:waypoint xsi:type="dc:Point" x="1203" y="707" />
            <di:waypoint xsi:type="dc:Point" x="1254" y="707" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="1183.5" y="697" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNShape id="EndEvent_1fx9yp3_di" bpmnElement="EndEvent_1fx9yp3">
            <dc:Bounds x="1418.2062726176116" y="689" width="36" height="36" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="1391.2062726176116" y="725" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNShape>
        <bpmndi:BPMNEdge id="SequenceFlow_0v64x8b_di" bpmnElement="SequenceFlow_0v64x8b">
            <di:waypoint xsi:type="dc:Point" x="1354" y="707" />
            <di:waypoint xsi:type="dc:Point" x="1418" y="707" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="1341" y="697" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        <bpmndi:BPMNEdge id="SequenceFlow_1ujhfx4_di" bpmnElement="SequenceFlow_1ujhfx4">
            <di:waypoint xsi:type="dc:Point" x="432" y="484" />
            <di:waypoint xsi:type="dc:Point" x="432" y="707" />
            <di:waypoint xsi:type="dc:Point" x="490" y="707" />
            <bpmndi:BPMNLabel>
            <dc:Bounds x="387" y="585.5" width="90" height="20" />
            </bpmndi:BPMNLabel>
        </bpmndi:BPMNEdge>
        </bpmndi:BPMNPlane>
    </bpmndi:BPMNDiagram>
    </bpmn:definitions>
    """
    
    query = "How many activities are there in this process?"
    # query = "What is the first activity in this process?"
    api_key = "your_api_key_here" 
    ai_model = "gemini-1.5-flash"
    ai_provider = "Google"

    response = generate_response_from_bpmn(bpmn_xml_content, query, api_key, ai_model, ai_provider)
    print(response)