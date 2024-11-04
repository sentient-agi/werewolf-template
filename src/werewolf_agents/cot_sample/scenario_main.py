# scenario_main.py

from sentient_campaign.agents.v1.message import (
    ActivityMessage,
    MimeType,
    ActivityMessageHeader,
    MessageChannelType,
    TextContent,
)

async def scenario_villager_discussion(agent):
    """Simulates a villager role discussing during the day."""
    # Simulate receiving the role from the moderator
    role_message = ActivityMessage(
        content_type=MimeType.TEXT_PLAIN,
        header=ActivityMessageHeader(
            message_id="1",
            sender=agent.MODERATOR_NAME,
            channel="direct",
            channel_type=MessageChannelType.DIRECT,
        ),
        content=TextContent(text="You are a villager."),
    )
    await agent.async_notify(role_message)

    # Simulate a group message in the GAME_CHANNEL
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
    await agent.async_notify(vote_message)

    # Have the agent respond to the vote message
    response = await agent.async_respond(vote_message)
    print(f"Agent vote response: {response.response}")

async def scenario_seer_night_action(agent):
    """Simulates the seer's night action."""
    # Simulate receiving the role from the moderator
    role_message = ActivityMessage(
        content_type=MimeType.TEXT_PLAIN,
        header=ActivityMessageHeader(
            message_id="4",
            sender=agent.MODERATOR_NAME,
            channel="direct",
            channel_type=MessageChannelType.DIRECT,
        ),
        content=TextContent(text="You are the seer."),
    )
    await agent.async_notify(role_message)

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
    response = await agent.async_respond(seer_night_message)
    print(f"Seer night action response: {response.response}")

async def scenario_doctor_night_action(agent):
    """Simulates the doctor's night action."""
    # Simulate receiving the role from the moderator
    role_message = ActivityMessage(
        content_type=MimeType.TEXT_PLAIN,
        header=ActivityMessageHeader(
            message_id="6",
            sender=agent.MODERATOR_NAME,
            channel="direct",
            channel_type=MessageChannelType.DIRECT,
        ),
        content=TextContent(text="You are the doctor."),
    )
    await agent.async_notify(role_message)

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
    response = await agent.async_respond(doctor_night_message)
    print(f"Doctor night action response: {response.response}")

async def scenario_wolf_group_action(agent):
    """Simulates the wolf's group discussion."""
    # Simulate receiving the role from the moderator
    role_message = ActivityMessage(
        content_type=MimeType.TEXT_PLAIN,
        header=ActivityMessageHeader(
            message_id="8",
            sender=agent.MODERATOR_NAME,
            channel="direct",
            channel_type=MessageChannelType.DIRECT,
        ),
        content=TextContent(text="You are a wolf."),
    )
    await agent.async_notify(role_message)

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
    await agent.async_notify(wolf_group_message)

    # Have the agent respond in the wolf's den
    response = await agent.async_respond(wolf_group_message)
    print(f"Wolf group action response: {response.response}")

# List of scenarios to be imported and run
SCENARIOS = [
    scenario_villager_discussion,
    scenario_seer_night_action,
    scenario_doctor_night_action,
    scenario_wolf_group_action,
]
