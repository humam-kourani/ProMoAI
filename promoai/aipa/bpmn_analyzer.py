import pm4py
from pm4py.objects.bpmn.obj import BPMN
from tempfile import NamedTemporaryFile
import os
import traceback 

from aipa.llm_connection import get_llm_chat_response 

from aipa.prompting import add_prompt_strategies
from aipa.conversation import create_message, create_conversation, create_process_model_representation


def bpmn_object_to_xml_string(bpmn_diagram: BPMN) -> str:
    temp_bpmn_file = NamedTemporaryFile(mode="w+", suffix=".bpmn", delete=False, encoding='utf-8')
    temp_file_path = temp_bpmn_file.name
    temp_bpmn_file.close()
    try:
        pm4py.write_bpmn(bpmn_diagram, temp_file_path)
        with open(temp_file_path, 'r', encoding='utf-8') as f:
            xml_string = f.read()
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
    return xml_string


class BPMNAnalyzer:
    def __init__(self, bpmn_xml_string: str, initial_query: str,
                 api_key: str, ai_model: str, ai_provider: str,
                 prompting_parameters: dict = None, selected_elements_json: str = None): 

        self.bpmn_xml_string = bpmn_xml_string
        self.api_key = api_key
        self.ai_model = ai_model
        self.ai_provider = ai_provider
        self.prompting_parameters = prompting_parameters if prompting_parameters is not None else {}
        self.selected_elements_json = selected_elements_json
        self.conversation = []

        # bpmn_xml_string = bpmn_object_to_xml_string(self.bpmn_diagram)
        
        # simplified_bpmn_text = get_simplified_xml_abstraction(bpmn_xml_string)

        system_prompt = add_prompt_strategies(parameters=self.prompting_parameters)

        print(system_prompt) # for debugging

        self.conversation = create_conversation(
            role="system",
            parameters=self.prompting_parameters
        )

        self.conversation.append(
            create_process_model_representation(
                model_content={"modelXmlString": bpmn_xml_string},
                role="system",
                parameters=self.prompting_parameters,
                selected_elements_json=self.selected_elements_json
        ))
        

        user_message_content = create_message(initial_query, role="user", parameters=self.prompting_parameters)
        self.conversation.append(user_message_content)
        
        try:
            _assistant_response_text, updated_conversation = get_llm_chat_response(
                conversation=self.conversation,
                api_key=self.api_key,
                llm_name=self.ai_model,
                ai_provider=self.ai_provider)           
            self.conversation = updated_conversation
        except Exception as e:
            print(f"Error during get_llm_chat_response call in __init__: {e}")
            traceback.print_exc()
            raise 

    def get_conversation(self):
        return self.conversation

    def get_last_response(self) -> str | None:
        if not self.conversation:
            return None
        
        for msg in reversed(self.conversation):
            if msg.get("role") == "assistant" or msg.get("role") == "user":
                return msg.get("content")
        return None

    def ask(self, follow_up_query: str) -> str | None:
        if not self.conversation:
            raise Exception("Conversation not initialized. Cannot ask a follow-up question.")

        self.conversation.append(
            {"role": "user", "content": follow_up_query}
        )

        try:
            _assistant_response_text, updated_conversation = get_llm_chat_response(
                conversation=self.conversation,
                api_key=self.api_key,
                llm_name=self.ai_model,
                ai_provider=self.ai_provider
            )
            self.conversation = updated_conversation
            return self.get_last_response()
 
        except Exception as e:
            print(f"Error during get_llm_chat_response call in ask: {e}")
            traceback.print_exc()
            return f"Error processing follow-up: {e}" 

    def generate_response(self):
        try:
            return self.get_last_response()
        except Exception as e:
            print(f"Error in generate_response_from_bpmn: {e}")
            traceback.print_exc()
            return None
