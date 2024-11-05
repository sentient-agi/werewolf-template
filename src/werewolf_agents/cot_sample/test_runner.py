# test_runner.py

import asyncio
import logging
import os
from dotenv import load_dotenv
from scenario_main import SCENARIOS
from datetime import datetime

# Import necessary classes
from agent.cot_agent import CoTAgent
from sentient_campaign.agents.v1.message import (
    ActivityMessage,
    ActivityMessageHeader,
    MimeType,
    MessageChannelType,
    TextContent,
)

load_dotenv()

# Set up logging (optional)
logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger("test_runner")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

def agent_factory():
    """Creates and initializes a new agent instance."""
    agent = CoTAgent()
    agent._sentient_llm_config = {
        "config_list": [
            {
                "llm_model_name": os.getenv("SENTIENT_DEFAULT_LLM_MODEL_NAME"),
                "api_key": os.getenv("MY_UNIQUE_API_KEY"),
                "llm_base_url": os.getenv("SENTIENT_DEFAULT_LLM_BASE_URL"),
            }
        ]
    }
    agent.__initialize__("Fred", "A werewolf player")
    return agent

def build_activity_message(agent, msg_data):
    """Builds an ActivityMessage from message data."""
    # Get message fields
    message_id = msg_data.get('message_id')
    sender = msg_data.get('sender')
    channel = msg_data.get('channel')
    channel_type_str = msg_data.get('channel_type')
    content_type_str = msg_data.get('content_type')
    text = msg_data.get('text')

    # Handle special channel names
    if sender == 'MODERATOR':
        sender = agent.MODERATOR_NAME
    if channel == 'GAME_CHANNEL':
        channel = agent.GAME_CHANNEL
    if channel == 'WOLFS_CHANNEL':
        channel = agent.WOLFS_CHANNEL

    # Convert channel_type and content_type to enums
    channel_type = getattr(MessageChannelType, channel_type_str)
    content_type = getattr(MimeType, content_type_str)

    header = ActivityMessageHeader(
        message_id=message_id,
        sender=sender,
        channel=channel,
        channel_type=channel_type,
    )
    content = TextContent(text=text)

    message = ActivityMessage(
        content_type=content_type,
        header=header,
        content=content,
    )
    return message

async def run_scenario(agent_factory, scenario):
    """Runs a given scenario using a new agent instance."""
    agent = agent_factory()
    messages = {}
    outputs = []
    message_history = []  # To store all messages

    # Capture the print statements
    import sys
    from io import StringIO

    original_stdout = sys.stdout
    sys.stdout = capture = StringIO()

    try:
        for step in scenario['steps']:
            action = step['action']
            if action == 'notify':
                msg_data = step['message']
                # Build the ActivityMessage
                message = build_activity_message(agent, msg_data)
                # Store the message by its message_id
                messages[message.header.message_id] = message
                message_history.append((message.header.sender, message.content.text))
                await agent.async_notify(message)
            elif action == 'respond':
                # For 'respond', we need to get the message to respond to
                if 'message_id' in step:
                    message_id = step['message_id']
                    message = messages.get(message_id)
                    if message is None:
                        print(f"Message ID {message_id} not found.")
                        continue
                elif 'message' in step:
                    # Build the message from data
                    msg_data = step['message']
                    message = build_activity_message(agent, msg_data)
                    # Store the message by its message_id
                    messages[message.header.message_id] = message
                else:
                    print("No message or message_id provided for respond action.")
                    continue
                response = await agent.async_respond(message)
                print(f"Agent response: {response.response}")
                outputs.append(f"Agent response: {response.response}")
                # Add agent's response to message history
                message_history.append((agent.name, response.response))
    except Exception as e:
        print(f"Error during scenario execution: {e}")

    # Restore original stdout
    sys.stdout = original_stdout

    return capture.getvalue(), message_history

async def main():
    """Main function to run all scenarios and save results to HTML."""
    results = []
    for scenario in SCENARIOS:
        logger.info(f"Running scenario: {scenario['name']}")
        output, message_history = await run_scenario(agent_factory, scenario)
        results.append({
            'scenario': scenario['name'],
            'description': scenario['description'],
            'output': output,
            'message_history': message_history,
        })

    # Generate HTML report
    generate_html_report(results)

def generate_html_report(results):
    """Generates an HTML report from the test results."""
    html_content = """
    <html>
    <head>
        <title>Scenario Test Results</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            h2 { color: #555; }
            p { color: #777; }
            pre { background-color: #f4f4f4; padding: 10px; border-radius: 5px; }
            .scenario { margin-bottom: 40px; }
        </style>
    </head>
    <body>
    """
    html_content += f"<h1>Scenario Test Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h1>"
    for result in results:
        html_content += f"""
        <div class="scenario">
            <h2>{result['scenario']}</h2>
            <p>{result['description']}</p>
            <h3>Message History:</h3>
            <pre>
        """
        # Exclude the first message (long introduction)
        message_history = result['message_history'][1:] if len(result['message_history']) > 1 else []
        for sender, text in message_history:
            html_content += f"{sender}: {text}\n"

        html_content += f"""</pre>
            <h3>Agent Output:</h3>
            <pre>{result['output']}</pre>
        </div>
        """
    html_content += "</body></html>"

    with open("scenario_main.html", "w") as f:
        f.write(html_content)
    print("Test results saved to scenario_main.html")

if __name__ == "__main__":
    asyncio.run(main())