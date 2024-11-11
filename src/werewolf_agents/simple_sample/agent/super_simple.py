from openai import OpenAI
import logging
from sentient_campaign.agents.v1.api import IReactiveAgent
from sentient_campaign.agents.v1.message import ActivityMessage, ActivityResponse, MimeType, ActivityMessageHeader, \
    MessageChannelType, TextContent
from retrying import retry

# Set up logging
logger = logging.getLogger("simple_agent")
level = logging.DEBUG
logger.setLevel(level)
logger.propagate = True
handler = logging.StreamHandler()
handler.setLevel(level)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class SimpleReactiveAgent(IReactiveAgent):

    def __init__(self):
        pass

    # initialize is a required method for the IReactiveAgent interface
    def __initialize__(self, name: str, description: str, config: dict = None):
        self._name = name
        self._description = description
        self._config = config or {}

        # This comes from the runner, it has a method to set these configs with a key you provide there:
        self.llm_config = self.sentient_llm_config["config_list"][0]
        self.openai_client = OpenAI(
            api_key=self.llm_config["api_key"],
            base_url=self.llm_config["llm_base_url"],
        )

        ########################### System Prompt ###########################
        # Here we create a simple list for storing message history
        # In the first entry of this list we put the system prompt.
        # The easiest way to modify this message is to edit this system prompt!

        self.message_history = [{
            "role": "system",
            "content": f"You are {self._name}. You are playing the conversational game of Werewolf, also known as Mafia. When prompted for any kind of vote, always vote for someone, if you refuse to vote you will be penalized."
        }]
        logger.debug(f"Initialized {self._name} with config: {self._config}")

    # this is another required method, this is the method that the game controller will call to notify your agent of something when no response is needed
    async def async_notify(self, message: ActivityMessage):
        # here we add the message to the message history, extracting relevant information from the ActivityMessage object it came in
        message_text = f"[From - {message.header.sender}| {message.header.channel}]: {message.content.text}"
        self.message_history.append({
            "role": "user",
            "content": message_text
        })
        logger.debug(f"Message added to history: {message_text}")

    @retry(stop_max_attempt_number=3, wait_fixed=4000)
    def completion_wrapper(self, model, messages):
        return self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
        )

    # this is a required method, this is the method that the game controller will call to notify your agent of something when a response is needed
    async def async_respond(self, message: ActivityMessage) -> ActivityResponse:
        message_text = f"[From - {message.header.sender}| {message.header.channel}]: {message.content.text}"
        self.message_history.append({
            "role": "user",
            "content": message_text
        })
        logger.debug(f"Message added to history: {message_text}")

        logger.debug("Generating response from OpenAI...")

        response = self.completion_wrapper(
            model=self.llm_config["llm_model_name"],
            messages=self.message_history,
        )

        assistant_message = f"[From {self._name} (me) | {message.header.channel}]: {response.choices[0].message.content}"
        self.message_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        logger.debug(f"Assistant response added to history: {assistant_message}")

        return ActivityResponse(response.choices[0].message.content)

# Testing the agent: Make sure to comment out this code when you want to actually run the agent in some games. 

# # Since we are not using the runner, we need to initialize the agent manually using an internal function:
# agent = SimpleReactiveAgent()
# agent._sentient_llm_config = {
#     "config_list": [{
#             "llm_model_name": "", # add model name here, should be: Llama31-70B-Instruct
#             "api_key": "", # add your api key here
#             "llm_base_url": "https://hp3hebj84f.us-west-2.awsapprunner.com"
#         }]  
# }
# agent.__initialize__("Fred", "A werewolf player")


# # Simulate receiving and responding to a message
# import asyncio

# async def main():
#     message = ActivityMessage(
#         content_type=MimeType.TEXT_PLAIN,
#         header=ActivityMessageHeader(
#             message_id="456",
#             sender="User",
#             channel="direct",
#             channel_type=MessageChannelType.DIRECT
#         ),
#         content=TextContent(text="Tell me about yourself")
#     )

#     response = await agent.async_respond(message)
#     print(f"Agent response: {response.response.text}")

# asyncio.run(main())
