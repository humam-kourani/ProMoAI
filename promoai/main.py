from pm4py import BPMN, convert_to_petri_net, discover_powl, PetriNet
from pm4py.algo.discovery.powl.inductive.variants.powl_discovery_varaints import (
    POWLDiscoveryVariant,
)

from promoai.model_generation.llm_model_generator import LLMProcessModelGenerator

from promoai.pn_to_powl.converter import convert_workflow_net_to_powl


def generate_model_from_text(
    description: str, api_key: str, ai_model: str, ai_provider: str
):
    return LLMProcessModelGenerator.from_description(
        description, api_key, ai_model, ai_provider
    )


def generate_model_from_event_log(event_log):
    powl_model = discover_powl(event_log, variant=POWLDiscoveryVariant.MAXIMAL)
    return LLMProcessModelGenerator.from_powl(powl_model=powl_model)


def generate_model_from_petri_net(pn: PetriNet):
    powl_model = convert_workflow_net_to_powl(pn)
    return LLMProcessModelGenerator.from_powl(powl_model=powl_model)


def generate_model_from_bpmn(bpmn_diagram: BPMN):
    pn, im, fm = convert_to_petri_net(bpmn_diagram)
    return generate_model_from_petri_net(pn)
