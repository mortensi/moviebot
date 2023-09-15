import json

import openai
import tiktoken

from src.common.config import AppConfig
from src.common.utils import search_by_crew, vss


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


def run_conversation(model, question):
    prompt = '''Use the provided information to answer the search query the user has sent. The search query may:
         - ask about a specific movie
         - get a recommendation based on the score
         - ask information related to certain movie
         - who is the director of a movie
         - if an actor appears in a specific movie
         - request a recommendation by genre
         - ask any kind of question related to movies except knowing in what movies does an actor appear
         
         In the previous cases, do not execute a function and do not try to answer the search query. 
         If the user wants to know the list of movies where an actor appears, you must execute the provided function, but only for this kind of question or similar.

        Search query: 

        {}
        '''.format(question)

    # Step 1: send the conversation and available functions to GPT
    system_msg = 'You are a smart and knowledgeable AI assistant with an expertise in all kind of movies. You are a very friendly and helpful AI. You are empowered to recommend movies based on the provided context. Do NOT make anything up. Do NOT engage in topics that are not about movies.';
    messages = [{"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}]
    functions = [
        {
            "name": "search_by_crew",
            "description": "Find if one or more actors appear in the movie crew",
            "parameters": {
                "type": "object",
                "properties": {
                    "actor": {
                        "type": "string",
                        "description": "The name of the actor or actress in the movie",
                    }
                },
                "required": ["actor"],
            },
        }
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        functions=functions,
        function_call="auto",  # auto is default, but we'll be explicit
    )
    response_message = response["choices"][0]["message"]

    # Step 2: check if GPT wanted to call a function
    if response_message.get("function_call"):
        print("A function needs to be invoked")
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "search_by_crew": search_by_crew,
        }  # only one function in this example, but you can have multiple
        function_name = response_message["function_call"]["name"]
        fuction_to_call = available_functions[function_name]
        function_args = json.loads(response_message["function_call"]["arguments"])
        function_response = fuction_to_call(
            crew=function_args.get("actor")
        )

        # Step 4: send the info on the function call and function response to GPT
        messages.append(response_message)  # extend conversation with assistant's reply
        messages.append(
            {
                "role": "function",
                "name": function_name,
                "content": function_response,
            }
        )  # extend conversation with function response
        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages,
        )  # get a new response from GPT where it can see the function response
        return second_response["choices"][0]["message"]["content"]
    else:
        print("No function needs be invoked")
        prompt = vss(model, question)
        return getOpenAIGPT35(prompt)
