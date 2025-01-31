import os
import shutil
import subprocess
import streamlit as st
import tempfile

import pm4py
from pm4py.algo.discovery.powl.inductive.variants.powl_discovery_varaints import POWLDiscoveryVariant
from pm4py.util import constants
from pm4py.objects.petri_net.exporter.variants.pnml import export_petri_as_string
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.bpmn import visualizer as bpmn_visualizer
from pm4py.objects.conversion.wf_net.variants.to_bpmn import apply as pn_to_bpmn
from pm4py.objects.bpmn.layout import layouter
from pm4py.objects.bpmn.exporter.variants.etree import get_xml_string

from promoai import llm_model_generator
from promoai.app_utils import InputType, ViewType, footer
from promoai.general_utils.ai_providers import AIProviders
from promoai.pn_to_powl.converter import convert_workflow_net_to_powl


def run_model_generator_app():
    subprocess.run(['streamlit', 'run', __file__])


def run_app():
    st.title('🤖 ProMoAI')

    st.subheader(
        "Process Modeling with Generative AI"
    )

    model_defaults = {
        AIProviders.GOOGLE.value: 'gemini-1.5-pro',
        AIProviders.OPENAI.value: 'gpt-4',
        AIProviders.DEEPSEEK.value: 'deepseek-reasoner',
        AIProviders.ANTHROPIC.value: 'claude-3-5-sonnet-latest',
        AIProviders.DEEPINFRA.value: 'meta-llama/Llama-3.2-90B-Vision-Instruct',
        AIProviders.MISTRAL_AI.value: 'mistral-large-latest'
    }

    model_help = {
        AIProviders.GOOGLE.value: "Enter a Google model name. You can get a **free Google API key** and check the latest models under: https://ai.google.dev/.",
        AIProviders.OPENAI.value: "Enter an OpenAI model name. You can get an OpenAI API key and check the latest models under: https://openai.com/pricing.",
        AIProviders.DEEPSEEK.value: "Enter a DeepSeek model name. You can get a DeepSeek API key and check the latest models under: https://api-docs.deepseek.com/.",
        AIProviders.ANTHROPIC.value: "Enter an Anthropic model name. You can get an Anthropic API key and check the latest models under: https://www.anthropic.com/api.",
        AIProviders.DEEPINFRA.value: "Enter a model name available through Deepinfra. DeepInfra supports popular open-source large language models like Meta's LLaMa and Mistral, and it also enables custom model deployment. You can get a Deepinfra API key and check the latest models under: https://deepinfra.com/models.",
        AIProviders.MISTRAL_AI.value: "Enter a Mistral AI model name. You can get a Mistral AI API key and check the latest models under: https://mistral.ai/."
    }

    temp_dir = "temp"

    if 'provider' not in st.session_state:
        st.session_state['provider'] = AIProviders.GOOGLE.value

    if 'model_name' not in st.session_state:
        st.session_state['model_name'] = model_defaults[st.session_state['provider']]

    def update_model_name():
        # if 'model_gen' in st.session_state:
        #     st.session_state.pop('model_gen')
        st.session_state['model_name'] = model_defaults[st.session_state['provider']]

    with st.expander("🔧 Configuration", expanded=True):
        provider = st.radio(
            "Choose AI Provider:",
            options=model_defaults.keys(),
            index=0,
            horizontal=True,
            help="Select the AI provider you'd like to use. Google offers the Gemini models,"
                 " which you can **try for free**,"
                 " while OpenAI provides GPT models. DeepInfra supports popular open-source large language models like"
                 " Meta's LLaMa and also enables custom model deployment. You can also try the models provided by"
                 " DeepSeek, Anthropic, and Mistral AI.",
            on_change=update_model_name,
            key='provider',
        )

        if 'model_name' not in st.session_state or st.session_state['provider'] != provider:
            st.session_state['model_name'] = model_defaults[provider]

        col1, col2 = st.columns(2)
        with col1:
            ai_model_name = st.text_input("Enter the AI model name:",
                                          key='model_name',
                                          help=model_help[st.session_state['provider']])
        with col2:
            api_key = st.text_input("API key:", type="password")

    if 'selected_mode' not in st.session_state:
        st.session_state['selected_mode'] = "Model Generation"

    input_type = st.radio("Select Input Type:",
                          options=[InputType.TEXT.value, InputType.MODEL.value, InputType.DATA.value], horizontal=True)

    if input_type != st.session_state['selected_mode']:
        st.session_state['selected_mode'] = input_type
        st.session_state['model_gen'] = None
        st.session_state['feedback'] = []
        st.rerun()

    with st.form(key='model_gen_form'):
        if input_type == InputType.TEXT.value:
            description = st.text_area("For **process modeling**, enter the process description:")
            # with st.expander("Show Optional Settings"):
            #     prompt_improvement = st.checkbox(
            #         label="Self-improve the process description",
            #         value=False,
            #         help="If enabled, the language model will self-improve the provided process description to make "
            #              "it richer and more detailed."
            #     )
            #     model_improvement = st.checkbox(
            #         "Self-improve the generated model",
            #         value=False,
            #         help="If enabled, the language model will self-evaluate the generated process model and"
            #              " potentially improve it accordingly."
            #     )
            submit_button = st.form_submit_button(label='Run')
            if submit_button:
                try:
                    # if prompt_improvement:
                    #     description = connection_utils.improve_process_description(description, api_key=api_key,
                    #                                                                openai_model=open_ai_model,
                    #                                                                api_url=api_url)

                    obj = llm_model_generator.initialize(description, api_key, ai_model_name, ai_provider=provider)

                    # if model_improvement:
                    #     feedback = model_self_improvement_prompt()
                    #     obj = llm_model_generator.update(obj, feedback, n_candidates=num_candidates,
                    #                                      api_key=api_key, openai_model=open_ai_model, api_url=api_url)

                    st.session_state['model_gen'] = obj
                    st.session_state['feedback'] = []
                except Exception as e:
                    st.error(body=str(e), icon="⚠️")
                    return

        elif input_type == InputType.DATA.value:
            uploaded_log = st.file_uploader("For **process model discovery**, upload an event log:",
                                            type=["xes", "xes.gz"],
                                            help="The event log will be used to generate a process model"
                                                 " using the POWL miner (see https://doi.org/10.1016/j.is.2024.102493).")
            submit_button = st.form_submit_button(label='Run')
            if submit_button:
                if uploaded_log is None:
                    st.error(body="No file is selected!", icon="⚠️")
                    return
                try:
                    contents = uploaded_log.read()
                    os.makedirs(temp_dir, exist_ok=True)
                    with tempfile.NamedTemporaryFile(mode="wb", delete=False,
                                                     dir=temp_dir, suffix=uploaded_log.name) as temp_file:
                        temp_file.write(contents)
                        log = pm4py.read_xes(temp_file.name)
                    shutil.rmtree(temp_dir, ignore_errors=True)

                    powl = pm4py.discover_powl(log, variant=POWLDiscoveryVariant.MAXIMAL)
                    obj = llm_model_generator.initialize(None, api_key=api_key,
                                                         powl_model=powl, llm_name=ai_model_name,
                                                         ai_provider=provider,
                                                         debug=False)
                    st.session_state['model_gen'] = obj
                    st.session_state['feedback'] = []
                except Exception as e:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    st.error(body=f"Error during discovery: {e}", icon="⚠️")
                    return
        elif input_type == InputType.MODEL.value:
            uploaded_file = st.file_uploader(
                "For **process model improvement**, upload a semi-block-structured BPMN or Petri net:",
                type=["bpmn", "pnml"]
            )
            submit_button = st.form_submit_button(label='Upload')
            if submit_button:
                if uploaded_file is None:
                    st.error(body="No file is selected!", icon="⚠️")
                    return
                else:
                    try:
                        file_extension = uploaded_file.name.split(".")[-1].lower()

                        if file_extension == "bpmn":
                            contents = uploaded_file.read()

                            os.makedirs(temp_dir, exist_ok=True)
                            with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".bpmn",
                                                             dir=temp_dir) as temp_file:
                                temp_file.write(contents)
                                bpmn_graph = pm4py.read_bpmn(temp_file.name)
                                pn, im, fm = pm4py.convert_to_petri_net(bpmn_graph)
                            shutil.rmtree(temp_dir, ignore_errors=True)

                        elif file_extension == "pnml":
                            contents = uploaded_file.read()

                            os.makedirs(temp_dir, exist_ok=True)
                            with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".bpmn",
                                                             dir=temp_dir) as temp_file:
                                temp_file.write(contents)
                                pn, im, fm = pm4py.read_pnml("temp.pnml")
                            shutil.rmtree(temp_dir, ignore_errors=True)

                        else:
                            st.error(body=f"Unsupported file format {file_extension}!", icon="⚠️")
                            return

                        # powl_code = pt_to_powl_code.recursively_transform_process_tree(process_tree)
                        # obj = llm_model_generator.initialize(None, api_key=api_key,
                        #                                      powl_model_code=powl_code, llm_name=ai_model_name,
                        #                                      ai_provider=provider,
                        #                                      debug=False)
                        powl = convert_workflow_net_to_powl(pn)
                        obj = llm_model_generator.initialize(None, api_key=api_key,
                                                             powl_model=powl, llm_name=ai_model_name,
                                                             ai_provider=provider,
                                                             debug=False)
                        st.session_state['model_gen'] = obj
                        st.session_state['feedback'] = []
                    except Exception as e:
                        if os.path.exists(temp_dir):
                            shutil.rmtree(temp_dir, ignore_errors=True)
                        st.error(body="Please upload a semi-block-structured model!", icon="⚠️")
                        return

    if 'model_gen' in st.session_state and st.session_state['model_gen']:

        st.success("Model generated successfully!", icon="🎉")

        col1, col2 = st.columns(2)

        try:
            with col1:
                with st.form(key='feedback_form'):
                    feedback = st.text_area("Feedback:", value="")
                    if st.form_submit_button(label='Update Model'):
                        try:
                            st.session_state['model_gen'] = llm_model_generator.update(st.session_state['model_gen'],
                                                                                       feedback,
                                                                                       api_key=api_key,
                                                                                       llm_name=ai_model_name,
                                                                                       ai_provider=provider)
                        except Exception as e:
                            raise Exception("Update failed! " + str(e))
                        st.session_state['feedback'].append(feedback)

                    if len(st.session_state['feedback']) > 0:
                        with st.expander("Feedback History", expanded=True):
                            i = 0
                            for f in st.session_state['feedback']:
                                i = i + 1
                                st.write("[" + str(i) + "] " + f + "\n\n")

            with col2:
                st.write("Export Model")
                powl = st.session_state['model_gen'].get_powl()
                pn, im, fm = pm4py.convert_to_petri_net(powl)
                bpmn = pn_to_bpmn(pn, im, fm)
                bpmn = layouter.apply(bpmn)

                download_1, download_2 = st.columns(2)
                with download_1:
                    bpmn_data = get_xml_string(bpmn,
                                               parameters={"encoding": constants.DEFAULT_ENCODING})
                    st.download_button(
                        label="Download BPMN",
                        data=bpmn_data,
                        file_name="process_model.bpmn",
                        mime="application/xml"
                    )

                with download_2:
                    pn_data = export_petri_as_string(pn, im, fm)
                    st.download_button(
                        label="Download PNML",
                        data=pn_data,
                        file_name="process_model.pnml",
                        mime="application/xml"
                    )

            view_option = st.selectbox("Select a view:", [v_type.value for v_type in ViewType])

            image_format = str("svg").lower()
            if view_option == ViewType.POWL.value:
                from pm4py.visualization.powl import visualizer
                powl = powl.simplify()
                vis_str = visualizer.apply(powl,
                                           parameters={'format': image_format})

            elif view_option == ViewType.PETRI.value:
                visualization = pn_visualizer.apply(pn, im, fm,
                                                    parameters={'format': image_format})
                vis_str = visualization.pipe(format='svg').decode('utf-8')
            else:  # BPMN
                visualization = bpmn_visualizer.apply(bpmn,
                                                      parameters={'format': image_format})
                vis_str = visualization.pipe(format='svg').decode('utf-8')

            with st.expander("View Image", expanded=True):
                st.image(vis_str)

        except Exception as e:
            st.error(icon='⚠️', body=str(e))


if __name__ == "__main__":
    st.set_page_config(
        page_title="ProMoAI",
        page_icon="🤖"
    )
    footer()
    run_app()
