import streamlit as st
from streamlit import session_state as ss
from openai_assistant import Assistant
import uuid  # To generate unique user IDs for session

# Function to get or generate a unique user ID
def get_user_id():
    if 'user_id' not in st.session_state:
        # Generate a unique user ID for the current session
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id

# Generate unique user ID for multi-tenant identification
user_id = get_user_id()

# Initialize Streamlit session state variables specific to the user
if f'agent_{user_id}' not in ss:
    ss[f'agent_{user_id}'] = Assistant()  # Initialize OpenAI assistant for this user
    ss[f'initial_message_shown_{user_id}'] = False  # Track if initial message was shown
    ss[f'chat_history_{user_id}'] = []  # Chat history for this user

# Configure the Streamlit app's appearance and settings
st.set_page_config(
    page_title="Brad Kenstler's Portfolio Chatbot",
    page_icon="🤖",
)

# App title displayed at the top of the page
st.title("🤖:blue[Brad Kenstler's Portfolio] :red[Agent]")

# Display the initial message from the assistant if not shown before
if not ss[f'initial_message_shown_{user_id}']:
    initial_message = (
        "Hi, I'm Brad Kenstler's website agent.\n\n"
        "I can answer any questions you may have about Brad's:\n"
        "* work experience\n"
        "* resume\n"
        "* project portfolio\n"
        "\nI can also help you get in touch with him.\n\n"
        "How can I assist you today?"
    )
    ss[f'initial_message_shown_{user_id}'] = True
    ss[f'chat_history_{user_id}'].append({"role": "assistant", "content": initial_message})

# Display chat messages from the chat history for the current user
for message in ss[f'chat_history_{user_id}']:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input and handle interactions
if prompt := st.chat_input("Tell me about Brad's experience in Applied AI."):
    # Display the user's message in the chat window
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add the user's message to the chat history
    ss[f'chat_history_{user_id}'].append({"role": "user", "content": prompt})

    # Send the user message to the assistant for processing
    ss[f'agent_{user_id}'].add_user_prompt("user", prompt)

    # Create an empty container to display the assistant's response
    with st.chat_message("assistant"):
        assistant_reply_box = st.empty()  # Placeholder for the assistant's reply

        # Stream the assistant's response in real-time and update the display
        assistant_reply = ss[f'agent_{user_id}'].stream_response(assistant_reply_box)

        # Once the response is fully streamed, add it to the chat history
        ss[f'chat_history_{user_id}'].append({"role": "assistant", "content": assistant_reply})
