from dotenv import load_dotenv
import openai
from openai.types.beta.assistant_stream_event import (
    ThreadMessageDelta, ThreadRunRequiresAction, ThreadMessageInProgress,
    ThreadMessageCompleted, ThreadRunCompleted
)
from openai.types.beta.threads.text_delta_block import TextDeltaBlock
from agent_functions import *
import json
import time
import os

# Load environment variables from a .env file
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv('OPENAI'))
model = 'gpt-4o'
assistant_id = 'asst_FihrukJSw8GEIpMQWGKLHTAG'


class Assistant:
    """
    A class that interacts with OpenAI GPT-4 API using threads and stream events.

    Attributes:
        thread_id (str): Class-level attribute that holds the current thread ID.
        client (OpenAI): OpenAI client initialized with API credentials.
        model (str): The model to use for interactions.
        assistant (dict): Assistant data retrieved from OpenAI API.
        thread (dict): The current thread used for message exchanges.
        run (dict): Holds run-related information.
        summary (str): Stores the summary of the assistant's output.
    """
    thread_id = ""

    def __init__(self, model: str = model):
        """
        Initializes the Assistant instance, retrieves assistant and thread data.

        Parameters:
            model (str): The model to use for generating responses (default: 'gpt-4o').
        """
        self.client = client
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None
        self.summary = None

        # Retrieve existing assistant based on hardcoded assistant ID
        self.assistant = self.client.beta.assistants.retrieve(assistant_id=assistant_id)

        # Create or retrieve the thread for message exchanges
        if Assistant.thread_id:
            self.thread = self.client.beta.threads.retrieve(thread_id=Assistant.thread_id)
        else:
            self.thread = self.client.beta.threads.create()
            Assistant.thread_id = self.thread.id

    def add_user_prompt(self, role: str, content: str):
        """
        Adds a user prompt (message) to the current thread.

        Parameters:
            role (str): The role of the message sender (e.g., 'user', 'system').
            content (str): The content of the message to send.
        """
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role=role,
                content=content
            )

    def stream_response(self, assistant_reply_box):
        """
        Streams the assistant's response in real-time and handles various events.

        Parameters:
            assistant_reply_box: The UI component to display the assistant's reply.

        Returns:
            str: The complete assistant reply or an error message.
        """
        try:
            with client.beta.threads.runs.create(
                    assistant_id=self.assistant.id,
                    thread_id=self.thread.id,
                    stream=True
            ) as stream:
                assistant_reply = ""
                start_time = time.time()
                max_duration = 120  # Set maximum duration for streaming in seconds

                # Iterate through the stream of events
                for event in stream:
                    print("Event received!")  # Debug statement

                    # Check for maximum duration timeout
                    if time.time() - start_time > max_duration:
                        print("Stream timeout exceeded.")
                        break

                    # Handle ThreadMessageDelta event (streaming content)
                    if isinstance(event, ThreadMessageDelta):
                        print("MSG ThreadMessageDelta event data")  # Debug statement
                        if isinstance(event.data.delta.content[0], TextDeltaBlock):
                            # Append and display new text
                            assistant_reply += event.data.delta.content[0].text.value
                            assistant_reply_box.markdown(assistant_reply)

                    # Handle ThreadRunRequiresAction event (tool actions required)
                    elif isinstance(event, ThreadRunRequiresAction):
                        print("ThreadRunRequiresAction event data")  # Debug statement

                        # List available runs and submit tool outputs
                        runs_page = self.client.beta.threads.runs.list(thread_id=self.thread.id)
                        runs = list(runs_page.data)
                        if runs:
                            run = runs[0]
                            run_id = run.id if hasattr(run, 'id') else None

                            if run_id:
                                required_actions = run.required_action.submit_tool_outputs.model_dump()
                                tool_outputs = []

                                # Execute required functions based on actions
                                for action in required_actions["tool_calls"]:
                                    func_name = action["function"]["name"]
                                    arguments = json.loads(action["function"]["arguments"])
                                    print(
                                        f"Executing function: {func_name} with arguments: {arguments}")  # Debug statement

                                    # Execute the agent function and collect output
                                    output = execute_required_function(func_name, arguments)
                                    print(f"Function {func_name} complete")  # Debug statement

                                    # Append tool output
                                    tool_outputs.append({
                                        "tool_call_id": action["id"],
                                        "output": str(output)
                                    })

                                # Submit tool outputs if available
                                if tool_outputs:
                                    print("Tool output acquired")
                                    with client.beta.threads.runs.submit_tool_outputs(
                                            thread_id=self.thread.id,
                                            run_id=run_id,
                                            tool_outputs=tool_outputs,
                                            stream=True
                                    ) as tool_stream:
                                        print("Streaming response to tool output...")

                                        # Handle events from tool output submission
                                        for tool_event in tool_stream:
                                            if isinstance(tool_event, ThreadMessageDelta):
                                                print("TOOL ThreadMessageDelta event data")  # Debug statement
                                                if isinstance(tool_event.data.delta.content[0], TextDeltaBlock):
                                                    assistant_reply += tool_event.data.delta.content[0].text.value
                                                    assistant_reply_box.markdown(assistant_reply)

                    # Handle other events
                    elif isinstance(event, ThreadMessageInProgress):
                        print("ThreadMessageInProgress event received")  # Debug statement
                        time.sleep(1)

                    elif isinstance(event, ThreadMessageCompleted):
                        print("Message completed.")  # Debug statement

                    elif isinstance(event, ThreadRunCompleted):
                        print("Run completed.")  # Debug statement

                    print("Loop iteration completed.")  # Debug statement to track progress

                return assistant_reply

        except Exception as e:
            print(f"An error occurred during streaming: {e}")
            return "An error occurred while processing your request."
