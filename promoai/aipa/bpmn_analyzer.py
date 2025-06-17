import traceback

from promoai.aipa.prompting import add_prompt_strategies
from promoai.aipa.conversation import create_message, create_conversation, create_process_model_representation
from promoai.general_utils.llm_connection import generate_response_with_history, query_llm


class BPMNAnalyzer:
    def __init__(self,
                 api_key: str, ai_model: str, ai_provider: str,
                 initial_query: str,
                 bpmn_xml_string: str= None,
                 bpmn_json_string: str= None,
                 selected_elements_json: str = None,
                 model_abstraction="simplified_xml",
                 enable_role_prompting=True,
                 enable_natural_language_restriction=True,
                 enable_chain_of_thought=False,
                 enable_process_analysis=False,
                 enable_knowledge_injection=False,
                 enable_few_shots_learning=False,
                 enable_negative_prompting=False,
                 enable_examples=True
        ):

        self.api_key = api_key
        self.ai_model = ai_model
        self.ai_provider = ai_provider
        self.model_abstraction = model_abstraction
        self.conversation = create_conversation(
            role="system",
            model_abstraction=model_abstraction,
            enable_role_prompting=enable_role_prompting,
            enable_natural_language_restriction=enable_natural_language_restriction,
            enable_chain_of_thought=enable_chain_of_thought,
            enable_process_analysis=enable_process_analysis,
            enable_knowledge_injection=enable_knowledge_injection,
            enable_few_shots_learning=enable_few_shots_learning,
            enable_negative_prompting=enable_negative_prompting,
            enable_examples=enable_examples
        )

        self.conversation.append(
            create_process_model_representation(model_abstraction=model_abstraction,
                                                role= "system",
                                                xml_string = bpmn_xml_string,
                                                json_abstraction = bpmn_json_string,
                                                selected_elements_json = selected_elements_json)
        )

        self.last_response = None
        self.ask(initial_query)

    def get_conversation(self):
        return self.conversation

    def get_last_response(self) -> str | None:
        return self.last_response

    def ask(self, query: str) -> str | None:

        user_message_content = create_message(query, role="user", model_abstraction=self.model_abstraction)
        self.conversation.append(user_message_content)

        self.last_response = query_llm(
            conversation=self.conversation,
            api_key=self.api_key,
            llm_name=self.ai_model,
            ai_provider=self.ai_provider)
        self.conversation.append({"role": "assistant", "content": self.last_response})
