from enum import Enum
import streamlit as st


class InputType(Enum):
    TEXT = "Text"
    MODEL = "Model"
    DATA = "Data"


class ViewType(Enum):
    PETRI = "Petri Net"
    BPMN = "BPMN"
    POWL = "POWL"


def footer():
    style = """
        <style>
          .footer-container { 
              position: fixed;
              left: 0;
              bottom: 0;
              width: 100%;
              text-align: center;
              padding: 15px 0;
              background-color: white;
              border-top: 2px solid lightgrey;
              z-index: 100;
          }

          .footer-text, .header-text {
              margin: 0;
              padding: 0;
          }
          .footer-links {
              margin: 0;
              padding: 0;
          }
          .footer-links a {
              margin: 0 10px;
              text-decoration: none;
              color: blue;
          }
          .footer-links img {
              vertical-align: middle;
          }
        </style>
        """

    foot = f"""
        <div class='footer-container'>
            <div class='footer-text'>
                Developed by 
                <a href="https://www.linkedin.com/in/humam-kourani-98b342232/" target="_blank" style="text-decoration:none;">Humam Kourani</a>
                and 
                <a href="https://www.linkedin.com/in/alessandro-berti-2a483766/" target="_blank" style="text-decoration:none;">Alessandro Berti</a>
                at the
                <a href="https://www.fit.fraunhofer.de/" target="_blank" style="text-decoration:none;">Fraunhofer Institute for Applied Information Technology FIT</a>.
            </div>
            <div class='footer-links'>
                <a href="https://doi.org/10.24963/ijcai.2024/1014" target="_blank">
                    <img src="https://img.shields.io/badge/ProMoAI:%20Process%20Modeling%20with%20Generative%20AI-gray?logo=googledocs&logoColor=white&labelColor=red" alt="ProMoAI Paper">
                </a>
                <a href="mailto:humam.kourani@fit.fraunhofer.de?cc=a.berti@pads.rwth-aachen.de;" target="_blank">
                    <img src="https://img.shields.io/badge/Email-gray?logo=minutemailer&logoColor=white&labelColor=green" alt="Email Humam Kourani">
                </a>
            </div>
        </div>
        """

    st.markdown(style, unsafe_allow_html=True)
    st.markdown(foot, unsafe_allow_html=True)