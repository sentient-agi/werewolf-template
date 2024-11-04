import asyncio
import logging

# Import the agent class from your module
from agent.cot_agent import CoTAgent

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
logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger("test_script")
logger.setLevel(logging.INFO)
logger.propagate = True
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

async def main():
    # Create an instance of the agent
    agent = CoTAgent()

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

    # Simulate receiving the role from the moderator
    role_message = ActivityMessage(
        content_type=MimeType.TEXT_PLAIN,
        header=ActivityMessageHeader(
            message_id="1",
            sender=agent.MODERATOR_NAME,  # 'moderator' by default
            channel="direct",
            channel_type=MessageChannelType.DIRECT,
        ),
        content=TextContent(text="You are a villager."),
    )

    # Notify the agent of the role message
    await agent.async_notify(role_message)

    # Now, simulate a group message in the GAME_CHANNEL
    group_message = ActivityMessage(
        content_type=MimeType.TEXT_PLAIN,
        header=ActivityMessageHeader(
            message_id="2",
            sender="Alice",
            channel=agent.GAME_CHANNEL,
            channel_type=MessageChannelType.GROUP,
        ),
        content=TextContent(text="I think Bob is acting suspicious."),
    )

    # Notify the agent of the group message
    await agent.async_notify(group_message)

    # Have the agent respond to the group message
    response = await agent.async_respond(group_message)
    print(f"Agent response: {response.response}")

    # Simulate the moderator asking for votes
    vote_message = ActivityMessage(
        content_type=MimeType.TEXT_PLAIN,
        header=ActivityMessageHeader(
            message_id="3",
            sender=agent.MODERATOR_NAME,
            channel=agent.GAME_CHANNEL,
            channel_type=MessageChannelType.GROUP,
        ),
        content=TextContent(text="It's time to vote. Who do you think is the werewolf?"),
    )

    # Notify the agent of the vote message
    await agent.async_notify(vote_message)

    # Have the agent respond to the vote message
    response = await agent.async_respond(vote_message)
    print(f"Agent vote response: {response.response}")

    # Extend the test to simulate night actions for different roles
    # Let's test for the 'seer' role
    role_message_seer = ActivityMessage(
        content_type=MimeType.TEXT_PLAIN,
        header=ActivityMessageHeader(
            message_id="4",
            sender=agent.MODERATOR_NAME,
            channel="direct",
            channel_type=MessageChannelType.DIRECT,
        ),
        content=TextContent(text="You are the seer."),
    )

    # Reinitialize the agent for a new role
    agent.__initialize__("Fred", "A werewolf player")  # Reset the agent
    await agent.async_notify(role_message_seer)

    # Simulate the moderator asking the seer for a night action
    seer_night_message = ActivityMessage(
        content_type=MimeType.TEXT_PLAIN,
        header=ActivityMessageHeader(
            message_id="5",
            sender=agent.MODERATOR_NAME,
            channel="direct",
            channel_type=MessageChannelType.DIRECT,
        ),
        content=TextContent(text="Who would you like to investigate tonight?"),
    )

    # Have the agent respond to the seer night action
    response = await agent.async_respond(seer_night_message)
    print(f"Seer night action response: {response.response}")

    # Similarly, test for the 'doctor' role
    role_message_doctor = ActivityMessage(
        content_type=MimeType.TEXT_PLAIN,
        header=ActivityMessageHeader(
            message_id="6",
            sender=agent.MODERATOR_NAME,
            channel="direct",
            channel_type=MessageChannelType.DIRECT,
        ),
        content=TextContent(text="You are the doctor."),
    )

    # Reinitialize the agent for a new role
    agent.__initialize__("Fred", "A werewolf player")  # Reset the agent
    await agent.async_notify(role_message_doctor)

    # Simulate the moderator asking the doctor for a night action
    doctor_night_message = ActivityMessage(
        content_type=MimeType.TEXT_PLAIN,
        header=ActivityMessageHeader(
            message_id="7",
            sender=agent.MODERATOR_NAME,
            channel="direct",
            channel_type=MessageChannelType.DIRECT,
        ),
        content=TextContent(text="Who would you like to protect tonight?"),
    )

    # Have the agent respond to the doctor night action
    response = await agent.async_respond(doctor_night_message)
    print(f"Doctor night action response: {response.response}")

    # Finally, test for the 'wolf' role
    role_message_wolf = ActivityMessage(
        content_type=MimeType.TEXT_PLAIN,
        header=ActivityMessageHeader(
            message_id="8",
            sender=agent.MODERATOR_NAME,
            channel="direct",
            channel_type=MessageChannelType.DIRECT,
        ),
        content=TextContent(text="You are a wolf."),
    )

    # Reinitialize the agent for a new role
    agent.__initialize__("Fred", "A werewolf player")  # Reset the agent
    await agent.async_notify(role_message_wolf)

    # Simulate a group message in the wolf's den
    wolf_group_message = ActivityMessage(
        content_type=MimeType.TEXT_PLAIN,
        header=ActivityMessageHeader(
            message_id="9",
            sender="WolfAlice",
            channel=agent.WOLFS_CHANNEL,
            channel_type=MessageChannelType.GROUP,
        ),
        content=TextContent(text="Who should we eliminate tonight?"),
    )

    # Notify the agent of the wolf group message
    await agent.async_notify(wolf_group_message)

    # Have the agent respond in the wolf's den
    response = await agent.async_respond(wolf_group_message)
    print(f"Wolf group action response: {response.response}")

if __name__ == "__main__":
    asyncio.run(main())
