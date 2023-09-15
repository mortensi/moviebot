import streamlit as st
import uuid
from sentence_transformers import SentenceTransformer
from common.config import AppConfig
from dotenv import load_dotenv
from common.utils import vss, store_conversation, moviebot_init
from src.common.llm import getOpenAIGPT35, run_conversation

# Load Global env
load_dotenv()
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
moviebot_init()


if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex


def render():
    st.title("The Movie Database")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if question := st.chat_input("Search the movie database"):
        # Display user message in chat message container and user message to chat history
        st.chat_message("user").markdown(question)
        st.session_state.messages.append({"role": "user", "content": question})

        # Build response
        prompt = vss(model, question)
        response = getOpenAIGPT35(prompt)

        # If you would like to experiment with OpenAI function invokation, comment the previous two lines and uncomment the following
        # response = run_conversation(model, question)

        # Store the interaction
        #store_conversation(question, prompt, response)

        # Display assistant response in chat message container and add assistant response to chat history
        st.chat_message("assistant").markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    render()
