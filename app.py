import streamlit as st
import json
from PIL import Image
import logging
import httpx
import openai
import json
import os

# Set your API key here
api_key = st.secrets['api_key']
openai.api_key = api_key
client = openai
assistant_id = st.secrets['assistant_id']

assistant=client.beta.assistants.retrieve(assistant_id)

def initialize_client():
    """
    Initialize the OpenAI client and retrieve the assistant.
    """
    client = openai
    assistant = client.beta.assistants.retrieve(assistant_id)
    return client, assistant.id

def create_thread(client):
    """
    Create a new thread for a user conversation.
    """
    thread= client.beta.threads.create()
    return thread.id

def add_message_to_thread(client, thread_id, user_message):
    """
    Add a user's message to the specified thread.
    """
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message
    )
    return message.id

def run_conversation(client, thread_id, assistant_id):
    """
    Run the conversation through the assistant and wait for completion.
    """
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions=""
    )

    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        if run.status == "completed":
            break

    return run.id

def get_conversation_messages(client, thread_id):
    """
    Retrieve all messages from a conversation thread.
    """
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    message_json = messages.model_dump()
    for msg in messages.data:
        return (msg.content[0].text.value)

def get_run_steps(client, thread_id, run_id):
    """
    Retrieve the steps of a run.
    """
    run_steps = client.beta.threads.runs.steps.list(
        thread_id=thread_id,
        run_id=run_id
    )
    run_steps_json = run_steps.model_dump()
    return run_steps_json

def save_conversation_to_file(data, filename):
    """
    Save conversation data to a JSON file.
    """
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# Initialize the OpenAI client and retrieve the assistant
client, assistant_id = initialize_client()
 # Create a new thread for the conversation
thread_id = create_thread(client)


# Define a custom filter to exclude HTTP request log messages
class ExcludeHttpFilter(logging.Filter):
    def filter(self, record):
        # Exclude log messages related to HTTP requests
        return "httpx" not in record.name

# Configure the logger for the root logger only
logging.basicConfig(
    level=logging.INFO,  # Set the desired logging level (e.g., INFO, DEBUG)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log',  # Specify the log file name
)


# Create a logger for the Streamlit app (the root logger)
logger = logging.getLogger()

# Add the custom filter to exclude HTTP request log messages
logger.addFilter(ExcludeHttpFilter())



def ask_openai(question):
    # Add user's message to the thread
    add_message_to_thread(client, thread_id, question)

    # Run the conversation through the assistant
    run_id = run_conversation(client, thread_id, assistant_id)

    # Retrieve all messages from the conversation thread
    messages = get_conversation_messages(client, thread_id)
    return messages



def main():
    st.set_option('deprecation.showfileUploaderEncoding', False)
    
    with st.sidebar:
        logo = Image.open("logo.png")
        st.image(logo, width=250)
        
        st.markdown("---")
        st.markdown("# About")
        st.markdown(
            "Open AI Assitant which is trained on the Product Reviews data using RAG and vector database"            
        )
        st.markdown(
            "Ask a question regarding a Product to summarize the reviews."
        )
        st.markdown(
            "For Go-to-Market (GTM) teams, this tool can rapidly distill key insights from extensive customer feedback, enabling swift strategic adjustments. Marketing teams can leverage the AI-generated summaries to craft targeted campaigns and messaging that resonate with customer sentiments and preferences. Product teams benefit by gaining a clear, concise understanding of customer needs and pain points, which can guide product development and innovation. Similarly, sales teams can use these summaries to understand customer preferences and objections more effectively, enhancing their sales strategies and communication. Overall, the Large Language Model (LLMs) provide a unified, efficient, and insightful approach to handling customer feedback, driving coherence and informed decision-making across sales, marketing, and product development efforts."
        )

    st.title("💬 Product Review Assistant")
    

    # Log an informational message from the root logger
    logger.info("User visited the homepage.")

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "Hi! I'm your product reviews assistant. How can I help you today?"}]

    for msg in st.session_state["messages"]:
        st.chat_message(msg["role"]).write(msg["content"])

    user_input = st.chat_input("Ask a question:")
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)
        response = ask_openai(user_input)

        # Log user interactions from the root logger
        logger.info(f"User input: {user_input}")
        logger.info(f"Assistant response: {response}")

        st.session_state["messages"].append({"role": "assistant", "content": response})
        st.chat_message("assistant").write(response)

if __name__ == "__main__":
    main()
