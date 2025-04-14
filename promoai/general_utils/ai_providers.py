from enum import Enum


class AIProviders(Enum):
    GOOGLE = "Google"
    OPENAI = "OpenAI"
    DEEPSEEK = "DeepSeek"
    ANTHROPIC = "Anthropic"
    DEEPINFRA = "Deepinfra"
    MISTRAL_AI = "Mistral AI"


AI_MODEL_DEFAULTS = {
    AIProviders.GOOGLE.value: "gemini-2.5-pro-exp-03-25",
    AIProviders.OPENAI.value: "gpt-4",
    AIProviders.DEEPSEEK.value: "deepseek-reasoner",
    AIProviders.ANTHROPIC.value: "claude-3-5-sonnet-latest",
    AIProviders.DEEPINFRA.value: "meta-llama/Llama-3.2-90B-Vision-Instruct",
    AIProviders.MISTRAL_AI.value: "mistral-large-latest",
}

DEFAULT_AI_PROVIDER = AIProviders.GOOGLE.value

AI_HELP_DEFAULTS = {
    AIProviders.GOOGLE.value: "Enter a Google model name. You can get a **free Google API key** and check the latest models under: https://ai.google.dev/.",
    AIProviders.OPENAI.value: "Enter an OpenAI model name. You can get an OpenAI API key and check the latest models under: https://openai.com/pricing.",
    AIProviders.DEEPSEEK.value: "Enter a DeepSeek model name. You can get a DeepSeek API key and check the latest models under: https://api-docs.deepseek.com/.",
    AIProviders.ANTHROPIC.value: "Enter an Anthropic model name. You can get an Anthropic API key and check the latest models under: https://www.anthropic.com/api.",
    AIProviders.DEEPINFRA.value: "Enter a model name available through Deepinfra. DeepInfra supports popular open-source large language models like Meta's LLaMa and Mistral, and it also enables custom model deployment. You can get a Deepinfra API key and check the latest models under: https://deepinfra.com/models.",
    AIProviders.MISTRAL_AI.value: "Enter a Mistral AI model name. You can get a Mistral AI API key and check the latest models under: https://mistral.ai/.",
}

MAIN_HELP = (
    "Select the AI provider you'd like to use. Google offers the Gemini models,"
    " which you can **try for free**,"
    " while OpenAI provides GPT models. DeepInfra supports popular open-source large language models like"
    " Meta's LLaMa and also enables custom model deployment. You can also try the models provided by"
    " DeepSeek, Anthropic, and Mistral AI."
)
