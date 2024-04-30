import subprocess

import streamlit as st
import textwrap 

from utils import LLMProcessModelGenerator
from utils.petrinet.to_petri_net import apply as powl_to_pn

from pm4py.util import constants
from utils.petrinet.pnml import export_petri_as_string
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.bpmn import visualizer as bpmn_visualizer
from pm4py.objects.conversion.wf_net.variants.to_bpmn import apply as pn_to_bpmn
from utils.bpmn.graphviz import layouter
from pm4py.objects.bpmn.exporter.variants.etree import get_xml_string


def run_model_generator_app():
    subprocess.run(['streamlit', 'run', __file__])


def run_app():
    st.title('🤖 ProMoAI')

    st.subheader(
        "Process Model Generator with Generative AI"
    )

    with st.form(key='model_gen_form'):
        col1, col2 = st.columns(2)

        with col1:
            open_ai_model = st.text_input("Enter the OpenAI model name:", value="gpt-4",
                                          help="You can check the latest models under: https://openai.com/pricing")

        with col2:
            api_key = st.text_input("Enter your OpenAI API key:", type="password")

        description = st.text_area("Enter the process description:")
        submit_button = st.form_submit_button(label='Run')

    if submit_button:
        try:
            st.session_state['model_gen'] = LLMProcessModelGenerator(description, api_key, open_ai_model)
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
                bpmn = layouter(bpmn)

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
        [![Paper](https://img.shields.io/badge/ProMoAI:%20Process%20Modeling%20with%20Generative%20AI-gray?logo=adobeacrobatreader&labelColor=red)](https://arxiv.org/abs/2403.04327)
    """), unsafe_allow_html=True)

if __name__ == "__main__":
    st.set_page_config(
        page_title="ProMoAI",
        page_icon="🤖"
    )
    run_app()
