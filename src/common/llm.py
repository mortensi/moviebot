import openai
import tiktoken

from src.common.config import AppConfig


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def getOpenAIGPT35(prompt):
    # Define the system message
    system_msg = 'You are a smart and knowledgeable AI assistant with an expertise in all kind of movies. You are a very friendly and helpful AI. You are empowered to recommend movies based on the provided context. Do NOT make anything up. Do NOT engage in topics that are not about movies.';

    encoding = tiktoken.encoding_for_model(AppConfig.OPENAI_MODEL)
    print("tokens: " + str(num_tokens_from_string(prompt, "cl100k_base")))

    try:
        response = openai.ChatCompletion.create(model=AppConfig.OPENAI_MODEL,
                                                stream=False,
                                                messages=[{"role": "system", "content": system_msg},
                                                          {"role": "user", "content": prompt}])
        return response["choices"][0]["message"]["content"]
    except openai.error.OpenAIError as e:
        # Handle the error here
        if "context window is too large" in str(e):
            print("Error: Maximum context length exceeded. Please shorten your input.")
            return "Maximum context length exceeded"
        else:
            print("An unexpected error occurred:", e)
            return "An unexpected error occurred"