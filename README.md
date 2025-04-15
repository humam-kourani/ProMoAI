# ProMoAI
ProMoAI leverages Large Language Models for the automatic generation of process models. ProMoAI transforms textual descriptions of processes into process models that can be exported in the BPMN and PNML formats. It also supports user interaction by providing feedback on the generated model to refine it. ProMoAI supports three input types:
* *Text:* Provide the initial process description in natural language.
* *Process Model:* Start with an already existing semi-block-structured BPMN or Petri net and use ProMoAI to refine it.
* *Event Log:* Start with an event log in the XES format and the initial process model will be derived using process discovery.

## Launching as a Streamlit App
You have two options for running ProMoAI.
* *On the cloud:* under https://promoai.streamlit.app/.
* *Locally:* by cloning this repository, installing the required environment and packages, and then running 'streamlit run app.py'.

## Installing as a Python Library
Run pip install promoai.

## Requirements

* *Environment:* the app is tested on both Python 3.9 and 3.10.
* *Dependencies:* all required dependencies are listed in the file 'requirements.txt'.
* *Packages:* all required packages are listed in the file 'packages.txt'.

## Running locally

### Requirements
    * [Python >=3.9, <3.11, !3.9.7](https://www.python.org/downloads/)
    * [Poetry](https://python-poetry.org)
### Setup
1. Install the above requirements.

2. Install the dependencies:
    To install all dependencies and ensure they match the `pyproject.toml` and `poetry.lock` files, run:

    ```sh
        poetry install --sync
    ```
3. Execute the following command to start the app:

    ```sh
    poetry run python -m streamlit run ./app.py
    ```
