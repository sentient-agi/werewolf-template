import logging

from openai import OpenAI
from retrying import retry
from sentient_campaign.agents.v1.api import IReactiveAgent
from sentient_campaign.agents.v1.message import (
    ActivityMessage,
    ActivityResponse,
    TextContent,
    MimeType,
    ActivityMessageHeader,
    MessageChannelType,
)
import asyncio

logger = logging.getLogger("simple_agent")
level = logging.DEBUG
logger.setLevel(level)
logger.propagate = True
handler = logging.StreamHandler()
handler.setLevel(level)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

GAME_CHANNEL = "play-arena"
WOLFS_CHANNEL = "wolf's-den"
MODERATOR_NAME = "moderator"


class SimpleUpdatedAgent(IReactiveAgent):

    def __init__(self):
        pass

    SPECIFIC_INSTRUCTIONS = {
        'villager': "You are a villager. Your goal is to eliminate the werewolves.\n"
                    "Villagers will lose if the number of villagers becomes equal to the number of werewolves.\n"
                    "At the beginning of the game, you can sometimes pretend to be the seer and claim you haven't found a werewolf yet, saying you've checked a dead player (if the real seer is still hidden) to deceive the werewolves.\n"
                    "The real seer will understand you're a decoy and may be more likely to survive the night.\n"
                    "If someone protects another player while accusing someone else, that accuser might be a wolf.\n",
        'seer': "You are the seer and in villagers team.\n"
                "Avoid exposing yourself to the werewolves, only do so if you're in immediate danger, so the doctor can save you.\n"
                "Your goal is to eliminate the werewolves.\n"
                "Villagers will lose if the number of villagers becomes equal to the number of werewolves.\n"
                "Each night, you can ask the moderator to check the role of one player.\n"
                "If a player openly claims to be a werewolf, avoid checking them, as villagers wouldn't claim that – instead, announce in public chat that a werewolf revealed themselves and should be voted out.\n"
                "If you see two players consistently supporting each other or voting against others, they may be werewolves, so consider checking them.\n"
                "If someone claims to be the seer, they might be a werewolf. Check them only near the end of the game, as villagers may try to protect you by diverting suspicion early on.\n"
                "If someone protects another player while accusing someone else, that accuser might be a wolf.\n",
        'doctor': "You are the doctor and in villagers team.\n"
                  "Avoid revealing yourself to the werewolves, only do so if you're in danger.\n"
                  "Your goal is to help eliminate the werewolves.\n"
                  "Villagers will lose if the number of villagers becomes equal to the number of werewolves.\n"
                  "Protect villagers and the seer when you think they're at risk and are not a werewolf.\n"
                  "Each night, you can ask the moderator to save one player.\n"
                  "If you notice two players consistently supporting each other or voting against villagers, they may be werewolves, so focus on saving other villagers.\n"
                  "If someone protects another player while accusing someone else, that accuser might be a wolf.\n",
        'wolf': "You are a werewolf. Your goal is to eliminate the villagers.\n"
                "When the number of werewolves equals the number of villagers, you win.\n"
                "You can communicate with other werewolves at night.\n"
                "Never reveal that you're a werewolf in the main game arena.\n"
                "At first, support villagers who attack suspected werewolves; avoid supporting fellow werewolves openly, as this will expose you.\n"
                "Later in the game, you can pretend to be the seer who checked a villager to influence votes against them.\n"
                "In the main game arena, avoid mentioning the names of your fellow werewolves to avoid drawing attention.\n"
                "Keep your response short and avoid arguing too much to stay under the radar.\n",
    }

    def __initialize__(self, name: str, description: str, config: dict = None):
        self._name = name
        self._description = description
        self._config = config or {}

        self.llm_config = self.sentient_llm_config["config_list"][0]
        self.openai_client = OpenAI(
            api_key=self.llm_config["api_key"],
            base_url=self.llm_config["llm_base_url"],
        )

        self.role = ''
        self.memory = "You are {self._name}\n"

        self.message_history = [{
            "role": "system",
            "content": f"You are {self._name}. You are playing the conversational game of Werewolf/Mafia. There are 4 villagers, 2 wolfs, seer, and doctor in this game."
        }]
        logger.info(f"Initialized {self._name} with config: {self._config}")

    async def async_notify(self, message: ActivityMessage):
        message_text = f"[From - {message.header.sender} in {message.header.channel}]: {message.content.text}"

        logger.info(f"ASYNC NOTIFY called with message: {message}")
        if message.header.channel_type == MessageChannelType.DIRECT and message.header.sender == MODERATOR_NAME:
            if not self.role:
                self.role = self.find_my_role(message)
                self.memory += f"Your role is {self.role}.\n"
                if self.role != "villager":
                    self.memory += "Don't expose yourself..\n"
                logger.info(f"Role found for user {self._name}: {self.role}")

                self.message_history.append({
                    "role": "system",
                    "content": self.SPECIFIC_INSTRUCTIONS[self.role]
                })

        self.message_history.append({
            "role": "user",
            "content": message_text
        })
        logger.info(f"async_notify Message added to history: {message_text}")

    async def async_respond(self, message: ActivityMessage) -> ActivityResponse:
        message_text = f"[From - {message.header.sender} in {message.header.channel}]: {message.content.text}"
        self.message_history.append({
            "role": "system",
            "content": message_text
        })
        self.message_history.append({
            "role": "system",
            "content": "You have to respond to this message. When prompted for any kind of vote by moderator, always vote for someone, if you refuse to vote you will be penalized."
        })
        logger.info(f"async_respond Message added to history: {message_text}")
        logger.info("Generating response from OpenAI...")

        response = self.completion_wrapper(
            model=self.llm_config["llm_model_name"],
            messages=self.message_history,
        )

        assistant_message = f"{response.choices[0].message.content}"
        self.message_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        logger.info(f"Assistant response added to history: {assistant_message}")

        return ActivityResponse(response.choices[0].message.content)

    @retry(stop_max_attempt_number=3, wait_fixed=4000)
    def completion_wrapper(self, model, messages):
        return self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
        )

    def find_my_role(self, message):
        response = self.completion_wrapper(
            model=self.llm_config["llm_model_name"],
            messages=[
                {
                    "role": "system",
                    "content": f"The user is playing a game of werewolf as user {self._name}, help the user with question with less than a line answer",
                },
                {
                    "role": "user",
                    "name": self._name,
                    "content": f"You have got message from moderator here about my role in the werewolf game, here is the message -> '{message.content.text}', what is your role? possible roles are 'wolf','villager','doctor' and 'seer'. answer in a few words.",
                },
            ],
        )
        my_role_guess = response.choices[0].message.content
        logger.info(f"my_role_guess: {my_role_guess}")

        role = None
        if "villager" in my_role_guess.lower():
            role = "villager"
        elif "seer" in my_role_guess.lower():
            role = "seer"
        elif "doctor" in my_role_guess.lower():
            role = "doctor"
        else:
            role = "wolf"

        if not role or role not in ["villager", "seer", "doctor", "wolf"]:
            raise Exception("Role not found")

        return role

#
# # Since we are not using the runner, we need to initialize the agent manually using an internal function:
# agent = SimpleReactiveAgent()
# agent._sentient_llm_config = {
#     "config_list": [{
#         "llm_model_name": "Llama31-70B-Instruct",
#         "api_key": "sk-QrPEW-u5E1MdkV9TzdcvNg",  # add your api key here
#         "llm_base_url": "https://hp3hebj84f.us-west-2.awsapprunner.com"
#     }]
# }
# agent.__initialize__("Fred", "A werewolf player")
#
#
# async def main():
#     message = ActivityMessage(
#         content_type=MimeType.TEXT_PLAIN,
#         header=ActivityMessageHeader(
#             message_id="456",
#             sender=MODERATOR_NAME,
#             channel="direct",
#             channel_type=MessageChannelType.DIRECT
#         ),
#         content=TextContent(text="Im assigning you as a werewolf.")
#     )
#     await agent.async_notify(message)
#
#     message = ActivityMessage(
#         content_type=MimeType.TEXT_PLAIN,
#         header=ActivityMessageHeader(
#             message_id="458",
#             sender="Fred",
#             channel="Play arena",
#             channel_type=MessageChannelType.GROUP
#         ),
#         content=TextContent(text="Hi, Im a villager. Tell me about yourself.")
#     )
#     response = await agent.async_respond(message)
#     print(f"Agent response: {response.response.text}")
#
#
# asyncio.run(main())
