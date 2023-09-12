import streamlit as st
import uuid
from sentence_transformers import SentenceTransformer
from config import AppConfig
from dotenv import load_dotenv
from common.utils import vss

# Load Global env
load_dotenv()
config = AppConfig()
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


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
    if prompt := st.chat_input("Search the movie database"):
        # Display user message in chat message container and user message to chat history
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Build response
        response = vss(model, prompt)

        # Display assistant response in chat message container and add assistant response to chat history
        st.chat_message("assistant").markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    render()
