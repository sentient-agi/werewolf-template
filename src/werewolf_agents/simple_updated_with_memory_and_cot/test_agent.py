import asyncio
import logging

# Import the agent class from your module
from agent.simple_updated_with_memory import SimpleReactiveAgent

# Import necessary classes
from sentient_campaign.agents.v1.message import (
    ActivityMessage,
    ActivityResponse,
    MimeType,
    ActivityMessageHeader,
    MessageChannelType,
    TextContent,
)
from dotenv import load_dotenv
import os

load_dotenv()

# Set up logging (optional)
logger = logging.getLogger("test_script")
level = logging.DEBUG
logger.setLevel(level)
logger.propagate = True
handler = logging.StreamHandler()
handler.setLevel(level)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

async def main():
    # Create an instance of the agent
    agent = SimpleReactiveAgent()

    # Set up the _sentient_llm_config attribute
    agent._sentient_llm_config = {
        "config_list": [
            {
                "llm_model_name": os.getenv("SENTIENT_DEFAULT_LLM_MODEL_NAME"),  # specify the model name
                "api_key": os.getenv("MY_UNIQUE_API_KEY"),    # replace with your OpenAI API key
                "llm_base_url": os.getenv("SENTIENT_DEFAULT_LLM_BASE_URL"),  # leave empty if using OpenAI's default base URL
            }
        ]
    }
    print(agent._sentient_llm_config)

    # Initialize the agent
    agent.__initialize__("Fred", "A werewolf player")

    # Simulate receiving and responding to a message
    message = ActivityMessage(
        content_type=MimeType.TEXT_PLAIN,
        header=ActivityMessageHeader(
            message_id="456",
            sender="User",
            channel="direct",
            channel_type=MessageChannelType.DIRECT,
        ),
        content=TextContent(text="Tell me about yourself"),
    )

    response = await agent.async_respond(message)
    print(f"Agent response: {response.response.text}")

if __name__ == "__main__":
    asyncio.run(main())
