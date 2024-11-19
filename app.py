import subprocess

import streamlit as st
import textwrap

from utils import LLMProcessModelGenerator
from pm4py.objects.conversion.powl.variants.to_petri_net import apply as powl_to_pn

from pm4py.util import constants
from pm4py.objects.petri_net.exporter.variants.pnml import export_petri_as_string
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.bpmn import visualizer as bpmn_visualizer
from pm4py.objects.conversion.wf_net.variants.to_bpmn import apply as pn_to_bpmn
from pm4py.objects.bpmn.layout import layouter
from pm4py.objects.bpmn.exporter.variants.etree import get_xml_string


def run_model_generator_app():
    subprocess.run(['streamlit', 'run', __file__])


def run_app():
    st.title('🤖 ProMoAI')

    st.subheader(
        "Process Model Generator with Generative AI"
    )

    model_defaults = {
        'Google': 'gemini-1.5-pro',
        'OpenAI': 'gpt-4',
        'Anthropic': 'claude-3-5-sonnet-latest',
        'Deepinfra': 'meta-llama/Llama-3.2-90B-Vision-Instruct',
        'Mistral AI': 'mistral-large-latest'
    }

    model_help = {
        'Google': "Enter a Google model name. You can get a **free Google API key** and check the latest models under: https://ai.google.dev/.",
        'OpenAI': "Enter an OpenAI model name. You can get an OpenAI API key and check the latest models under: https://openai.com/pricing.",
        'Anthropic': "Enter an Anthropic model name. You can get an Anthropic API key and check the latest models under: https://www.anthropic.com/api.",
        'Deepinfra': "Enter a model name available through Deepinfra. DeepInfra supports popular open-source large language models like Meta's LLaMa and Mistral, and it also enables custom model deployment. You can get a Deepinfra API key and check the latest models under: https://deepinfra.com/models.",
        'Mistral AI': "Enter a Mistral AI model name. You can get a Mistral AI API key and check the latest models under: https://mistral.ai/."
    }

    if 'provider' not in st.session_state:
        st.session_state['provider'] = 'Google'

    if 'model_name' not in st.session_state:
        st.session_state['model_name'] = model_defaults[st.session_state['provider']]

    def update_model_name():
        if 'model_gen' in st.session_state:
            st.session_state.pop('model_gen')
        st.session_state['model_name'] = model_defaults[st.session_state['provider']]

    provider = st.radio(
        "Choose AI Provider:",
        options=model_defaults.keys(),
        index=0,
        horizontal=True,
        help="Select the AI provider you'd like to use. Google offers the Gemini models, which you can **try for free**,"
             " while OpenAI provides GPT models and Anthropic provides Claude models. DeepInfra supports popular open-source large language models like"
             " Meta's LLaMa and also enables custom model deployment.",
        on_change=update_model_name,
        key='provider',
    )

    if 'model_name' not in st.session_state or st.session_state['provider'] != provider:
        st.session_state['model_name'] = model_defaults[provider]

    with st.form(key='model_gen_form'):

        col1, col2 = st.columns(2)

        with col1:
            open_ai_model = st.text_input("Enter the AI model name:",
                                          key='model_name',
                                          help=model_help[st.session_state['provider']])

        with col2:
            api_key = st.text_input("Enter your API key:", type="password")

        description = st.text_area("Enter the process description:")
        submit_button = st.form_submit_button(label='Run')

    if submit_button:
        try:
            st.session_state['model_gen'] = LLMProcessModelGenerator(description, api_key, open_ai_model, provider)
            st.session_state['feedback'] = []
        except Exception as e:
            st.error(body=str(e), icon="⚠️")
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
                            st.session_state['model_gen'].update(feedback)
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
                pn, im, fm = powl_to_pn(powl)
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

            view_option = st.selectbox("Select a view:", ["BPMN", "Petri net"])

            image_format = str("svg").lower()
            # if view_option == "POWL":
            #     from pm4py.visualization.powl import visualizer
            #     visualization = visualizer.apply(powl,
            #                                      parameters={'format': image_format})
            if view_option == "Petri net":
                visualization = pn_visualizer.apply(pn, im, fm,
                                                    parameters={'format': image_format})
            else:  # BPMN
                visualization = bpmn_visualizer.apply(bpmn,
                                                      parameters={'format': image_format})

            with st.expander("View Image", expanded=True):
                st.image(visualization.pipe(format='svg').decode('utf-8'))

        except Exception as e:
            st.error(icon='⚠', body=str(e))

    st.markdown("\n\n")

    st.markdown(textwrap.dedent("""
        [![LinkedIn](https://img.shields.io/badge/Humam%20Kourani-gray?logo=linkedin&labelColor=blue)](https://www.linkedin.com/in/humam-kourani-98b342232/)
        [![Email](https://img.shields.io/badge/Email-gray?logo=minutemailer&logoColor=white&labelColor=green)](mailto:humam.kourani@fit.fraunhofer.de)
    """), unsafe_allow_html=True)
    st.markdown(textwrap.dedent("""
        [![Paper](https://img.shields.io/badge/ProMoAI:%20Process%20Modeling%20with%20Generative%20AI-gray?logo=adobeacrobatreader&labelColor=red)](https://doi.org/10.24963/ijcai.2024/1014)
    """), unsafe_allow_html=True)


if __name__ == "__main__":
    st.set_page_config(
        page_title="ProMoAI",
        page_icon="🤖"
    )
    run_app()
