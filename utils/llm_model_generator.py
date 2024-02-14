from utils.prompting import create_conversation, update_conversation
from utils.model_generation.model_generation import generate_model
from pm4py.util import constants


class LLMProcessModelGenerator(object):
    def __init__(self, process_description: str, api_key: str,
                 openai_model: str = "gpt-3.5-turbo-0125"):  # gpt-4-0125-preview gpt-3.5-turbo-0125
        self.__api_key = api_key
        self.__openai_model = openai_model
        init_conversation = create_conversation(process_description)
        self.__process_model, self.__conversation = generate_model(init_conversation,
                                                                   api_key=self.__api_key,
                                                                   openai_model=self.__openai_model)

    def __to_petri_net(self):
        from pm4py.objects.conversion.powl.converter import apply as powl_to_pn
        net, im, fm = powl_to_pn(self.__process_model)
        return net, im, fm

    def get_powl(self):
        return self.__process_model

    def get_bpmn(self):
        net, im, fm = self.__to_petri_net()
        from pm4py.objects.conversion.wf_net.variants.to_bpmn import apply as pn_to_bpmn
        bpmn_model = pn_to_bpmn(net, im, fm)
        from pm4py.objects.bpmn.layout import layouter
        bpmn_model = layouter.apply(bpmn_model)
        return bpmn_model

    def update(self, feedback: str):
        self.__conversation = update_conversation(self.__conversation, feedback)
        self.__process_model, self.__conversation = generate_model(conversation=self.__conversation,
                                                                   api_key=self.__api_key,
                                                                   openai_model=self.__openai_model)

    def view_bpmn(self, image_format: str = "svg"):
        bpmn_model = self.get_bpmn()
        image_format = str(image_format).lower()
        from pm4py.visualization.bpmn import visualizer as bpmn_visualizer
        parameters = bpmn_visualizer.Variants.CLASSIC.value.Parameters
        visualization = bpmn_visualizer.apply(bpmn_model,
                                              parameters={parameters.FORMAT: image_format})
        bpmn_visualizer.view(visualization)

    def view_petri_net(self, image_format: str = "svg"):
        net, im, fm = self.__to_petri_net()
        image_format = str(image_format).lower()
        from pm4py.visualization.petri_net import visualizer as petri_net_visualizer
        parameters = petri_net_visualizer.Variants.WO_DECORATION.value.Parameters
        visualization = petri_net_visualizer.apply(net, im, fm,
                                                   parameters={parameters.FORMAT: image_format})
        petri_net_visualizer.view(visualization)

    def view_powl(self, image_format: str = "svg"):
        image_format = str(image_format).lower()
        from pm4py.visualization.powl import visualizer as powl_visualizer
        parameters = powl_visualizer.POWLVisualizationVariants.BASIC.value.Parameters
        visualization = powl_visualizer.apply(self.__process_model,
                                              parameters={parameters.FORMAT: image_format})
        powl_visualizer.view(visualization)

    def export_bpmn(self, file_path: str, encoding: str = constants.DEFAULT_ENCODING):
        if not file_path.lower().endswith("bpmn"):
            raise Exception("The provided file path does not have the '.bpmn' extension!")
        bpmn_model = self.get_bpmn()
        from pm4py.objects.bpmn.exporter import exporter
        exporter.apply(bpmn_model, file_path, parameters={"encoding": encoding})

    def export_petri_net(self, file_path: str, encoding: str = constants.DEFAULT_ENCODING):
        if not file_path.lower().endswith("pnml"):
            raise Exception("The provided file path does not have the '.pnml' extension!")
        net, im, fm = self.__to_petri_net()
        from pm4py.objects.petri_net.exporter import exporter as petri_exporter
        petri_exporter.apply(net=net,
                             initial_marking=im,
                             final_marking=fm,
                             output_filename=file_path,
                             parameters={"encoding": encoding})
