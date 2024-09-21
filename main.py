import streamlit as st
from streamlit import session_state as ss
from openai_assistant import Assistant

# Initialize Streamlit session state variables
if 'agent' not in ss:
    ss.agent = Assistant()  # Initialize the OpenAI assistant
    ss.initial_message_shown = False  # Flag to track if the initial message was shown
    ss.chat_history = []  # List to store chat history

# Configure the Streamlit app's appearance and settings
st.set_page_config(
    page_title="Brad Kenstler's Portfolio Chatbot",
    page_icon="🤖",
)

# App title displayed at the top of the page
st.title("🤖:blue[Brad Kenstler's Portfolio] :red[Agent]")

# Display the initial message from the assistant if not shown before
if not ss.initial_message_shown:
    initial_message = (
        "Hi, I'm Brad Kenstler's website agent.\n\n"
        "I can answer any questions you may have about Brad's:\n"
        "* work experience\n"
        "* resume\n"
        "* project portfolio\n"
        "\nI can also help you get in touch with him.\n\n"
        "How can I assist you today?"
    )
    ss.initial_message_shown = True
    ss.chat_history.append({"role": "assistant", "content": initial_message})

# Display chat messages from chat history on app rerun
for message in ss.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input and handle interactions
if prompt := st.chat_input("Tell me about Brad's experience in Applied AI."):
    # Display the user's message in the chat window
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add the user's message to the chat history
    ss.chat_history.append({"role": "user", "content": prompt})

    # Send the user message to the assistant for processing
    ss.agent.add_user_prompt("user", prompt)

    # Create an empty container to display the assistant's response
    with st.chat_message("assistant"):
        assistant_reply_box = st.empty()  # Placeholder for the assistant's reply

        # Stream the assistant's response in real-time and update the display
        assistant_reply = ss.agent.stream_response(assistant_reply_box)

        # Once the response is fully streamed, add it to the chat history
        ss.chat_history.append({"role": "assistant", "content": assistant_reply})
