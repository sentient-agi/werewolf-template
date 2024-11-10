from typing import Any, Dict

import os,json,re
import asyncio
import logging
from collections import defaultdict
import openai
from openai import RateLimitError, OpenAI
from sentient_campaign.agents.v1.api import IReactiveAgent
from sentient_campaign.agents.v1.message import (
    ActivityMessage,
    ActivityResponse,
    TextContent,
    MimeType,
    ActivityMessageHeader,
    MessageChannelType,
)
from tenacity import (
    retry,
    stop_after_attempt,
    retry_if_exception_type,
    wait_exponential,
)
GAME_CHANNEL = "play-arena"
WOLFS_CHANNEL = "wolf's-den"
MODERATOR_NAME = "moderator"
MODEL_NAME = "Llama31-70B-Instruct"

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger = logging.getLogger("demo_agent")
level = logging.DEBUG
logger.setLevel(level)
logger.propagate = True
handler = logging.StreamHandler()
handler.setLevel(level)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class CoTAgent(IReactiveAgent):
    # input -> thoughts -> init action -> reflection -> final action

    WOLF_PROMPT = """You are a wolf in a game of Werewolf. Your goal is to eliminate villagers without being detected. Consider the following:
    1. Blend in with villagers during day discussions.
    2. Coordinate with other werewolves to choose a target.
    3. Pay attention to the seer and doctor's potential actions.
    4. Defend yourself if accused, but don't be too aggressive."""

    VILLAGER_PROMPT = """You are a villager in a game of Werewolf. Your goal is to identify and eliminate the werewolves. Consider the following:
    1. Observe player behavior and voting patterns.
    2. Share your suspicions and listen to others.
    3. Be cautious of false accusations.
    4. Try to identify the seer and doctor to protect them."""

    SEER_PROMPT = """You are the seer in a game of Werewolf. Your ability is to learn one player's true identity each night. Consider the following:
    1. Use your knowledge wisely without revealing your role.
    2. Keep track of the information you gather each night.
    3. Guide village discussions subtly.
    4. Be prepared to reveal your role if it can save the village."""

    DOCTOR_PROMPT = """You are the doctor in a game of Werewolf. Your ability is to protect one player from elimination each night. Consider the following:
    1. Decide whether to protect yourself or others.
    2. Try to identify key players to protect (like the seer).
    3. Vary your protection pattern to avoid being predictable.
    4. Participate in discussions without revealing your role."""

    def __init__(self):
        logger.debug("WerewolfAgent initialized.")
        

    def __initialize__(self, name: str, description: str, config: dict = None):
        super().__initialize__(name, description, config)
        self._name = name
        self._description = description
        self.MODERATOR_NAME = MODERATOR_NAME
        self.WOLFS_CHANNEL = WOLFS_CHANNEL
        self.GAME_CHANNEL = GAME_CHANNEL
        self.config = config
        self.have_thoughts = True
        self.have_reflection = True
        self.role = None
        self.direct_messages = defaultdict(list)
        self.group_channel_messages = defaultdict(list)
        self.seer_checks = {}  # To store the seer's checks and results
        self.game_history = []  # To store the interwoven game history

        self.llm_config = self.sentient_llm_config["config_list"][0]
        self.openai_client = OpenAI(
            api_key=self.llm_config["api_key"],
            base_url=self.llm_config["llm_base_url"],
        )

        self.model = self.llm_config["llm_model_name"]
        logger.info(
            f"WerewolfAgent initialized with name: {name}, description: {description}, and config: {config}"
        )
        self.game_intro = None

    async def async_notify(self, message: ActivityMessage):
        logger.info(f"ASYNC NOTIFY called with message: {message}")
        if message.header.channel_type == MessageChannelType.DIRECT:
            user_messages = self.direct_messages.get(message.header.sender, [])
            user_messages.append(message.content.text)
            self.direct_messages[message.header.sender] = user_messages
            self.game_history.append(f"[From - {message.header.sender}| To - {self._name} (me)| Direct Message]: {message.content.text}")
            if not len(user_messages) > 1 and message.header.sender == self.MODERATOR_NAME:
                self.role = self.find_my_role(message)
                logger.info(f"Role found for user {self._name}: {self.role}")
        else:
            group_messages = self.group_channel_messages.get(message.header.channel, [])
            group_messages.append((message.header.sender, message.content.text))
            self.group_channel_messages[message.header.channel] = group_messages
            self.game_history.append(f"[From - {message.header.sender}| To - Everyone| Group Message in {message.header.channel}]: {message.content.text}")
            # if this is the first message in the game channel, the moderator is sending the rules, store them
            if message.header.channel == self.GAME_CHANNEL and message.header.sender == self.MODERATOR_NAME and not self.game_intro:
                self.game_intro = message.content.text
        logger.info(f"message stored in messages {message}")

    def get_interwoven_history(self, include_wolf_channel=False):
        return "\n".join([
            event for event in self.game_history
            if include_wolf_channel or not event.startswith(f"[{self.WOLFS_CHANNEL}]")
        ])

    @retry(
        wait=wait_exponential(multiplier=1, min=20, max=300),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(openai.RateLimitError),
    )
    def find_my_role(self, message):
        response = self.openai_client.chat.completions.create(
            model=self.model,
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
        if "villager" in my_role_guess.lower():
            role = "villager"
        elif "seer" in my_role_guess.lower():
            role = "seer"
        elif "doctor" in my_role_guess.lower():
            role = "doctor"
        else:
            role = "wolf"
        
        return role

    async def async_respond(self, message: ActivityMessage):
        logger.info(f"ASYNC RESPOND called with message: {message}")

        if message.header.channel_type == MessageChannelType.DIRECT and message.header.sender == self.MODERATOR_NAME:
            self.direct_messages[message.header.sender].append(message.content.text)
            if self.role == "seer":
                response_message = self._get_response_for_seer_guess(message)
            elif self.role == "doctor":
                response_message = self._get_response_for_doctors_save(message)
            
            response = ActivityResponse(response=response_message)
            self.game_history.append(f"[From - {message.header.sender}| To - {self._name} (me)| Direct Message]: {message.content.text}")
            self.game_history.append(f"[From - {self._name} (me)| To - {message.header.sender}| Direct Message]: {response_message}")    
        elif message.header.channel_type == MessageChannelType.GROUP:
            self.group_channel_messages[message.header.channel].append(
                (message.header.sender, message.content.text)
            )
            if message.header.channel == self.GAME_CHANNEL:
                response_message = self._get_discussion_message_or_vote_response_for_common_room(message)
            elif message.header.channel == self.WOLFS_CHANNEL:
                response_message = self._get_response_for_wolf_channel_to_kill_villagers(message)
            self.game_history.append(f"[From - {message.header.sender}| To - {self._name} (me)| Group Message in {message.header.channel}]: {message.content.text}")
            self.game_history.append(f"[From - {self._name} (me)| To - {message.header.sender}| Group Message in {message.header.channel}]: {response_message}")
        
        return ActivityResponse(response=response_message)

    def _get_inner_monologue(self, role_prompt, game_situation, specific_prompt):
        prompt = f"""{role_prompt}

Current game situation (including your past thoughts and actions): 
{game_situation}

{specific_prompt}"""

        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a {self.role} in a Werewolf game."},
                {"role": "user", "content": prompt}
            ]
        )
        inner_monologue = response.choices[0].message.content
        # self.game_history.append(f"\n [My Thoughts]: {inner_monologue}")

        logger.info(f"My Thoughts: {inner_monologue}")
        
        return inner_monologue

    def _get_final_action(self, role_prompt, game_situation, inner_monologue, action_type):
        prompt = f"""{role_prompt}

Current game situation (including past thoughts and actions): 
{game_situation}

Your thoughts:
{inner_monologue}

Based on your thoughts and the current situation, what is your {action_type}? Respond with only the {action_type} and no other sentences/thoughts. If it is a dialogue response, you can provide the full response that adds to the discussions so far. For all other cases a single sentence response is expected. If you are in the wolf-group channel, the sentence must contain the name of a person you wish to eliminate, and feel free to change your mind so that there is consensus. If you are in the game-room channel, the sentence must contain your response or vote, and it must be a vote to eliminate someone if the game moderator has recently messaged you asking for a vote, and also feel free to justify your vote, and later change your mind when the final vote count happens. You can justify any change of mind too. If the moderator for the reason behind the vote, you must provide the reason in the response."""

        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a {self.role} in a Werewolf game. Provide your final {action_type}."},
                {"role": "user", "content": prompt}
            ]
        )
        
        logger.info(f"My initial {action_type}: {response.choices[0].message.content}")
        initial_action = response.choices[0].message.content
        # do another run to reflect on the final action and do a sanity check, modify the response if need be
        prompt = f"""{role_prompt}

Current game situation (including past thoughts and actions):
{game_situation}

Your thoughts:
{inner_monologue}

Your initial action:
{response.choices[0].message.content}

Reflect on your final action given the situation and provide any criticisms. Answer the folling questions:
1. What is my name and my role ? 
2. Does my action align with my role and am I revealing too much about myself in a public channel? Does my action harm my team or my own interests?
3. Is my action going against what my objective is in the game?
3. How can I improve my action to better help the agents on my team and help me survive?"""
        
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a {self.role} in a Werewolf game. Reflect on your final action."},
                {"role": "user", "content": prompt}
            ]
        )

        logger.info(f"My reflection: {response.choices[0].message.content}")

         # do another run to reflect on the final action and do a sanity check, modify the response if need be
        prompt = f"""{role_prompt}

Current game situation (including past thoughts and actions):
{game_situation}

Your thoughts:
{inner_monologue}

Your initial action:
{initial_action}

Your reflection:
{response.choices[0].message.content}

Based on your thoughts, the current situation, and your reflection on the initial action, what is your absolute final {action_type}? Respond with only the {action_type} and no other sentences/thoughts. If it is a dialogue response, you can provide the full response that adds to the discussions so far. For all other cases a single sentence response is expected. If you are in the wolf-group channel, the sentence must contain the name of a person you wish to eliminate, and feel free to change your mind so that there is consensus. If you are in the game-room channel, the sentence must contain your response or vote, and it must be a vote to eliminate someone if the game moderator has recently messaged you asking for a vote, and also feel free to justify your vote, and later change your mind when the final vote count happens. You can justify any change of mind too. If the moderator for the reason behind the vote, you must provide the reason in the response. If the moderator asked for the vote, you must mention at least one name to eliminate. If the moderator asked for a final vote, you must answer in a single sentence the name of the person you are voting to eliminate even if you are not sure."""
        
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a {self.role} in a Werewolf game. Provide your final {action_type}."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content.strip("\n ")
    
    def _summarize_game_history(self):

        self.detailed_history = "\n".join(self.game_history)

        # send the llm the previous summary of each of the other players and suspiciona nd information, the detailed chats of this day or night
        # llm will summarize the game history and provide a summary of the game so far
        # summarized game history is used for current situation
           # Create a prompt for the Llama model to summarize the game history
        prompt = f"Summarize the following game history:\n\n{self.detailed_history}\n\nProvide a concise summary of the game so far."

        # Send the prompt to the Llama model and get the response
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a summarizer for a Werewolf game. Make sure to not miss any key information during summarization."},
                {"role": "user", "content": prompt}
            ]
        )

        # Extract the summarized game history from the response
        self.summarized_game_history = response.choices[0].message.content.strip("\n ")

        return self.summarized_game_history
        

        #pass


    def _get_response_for_seer_guess(self, message):
        seer_checks_info = "\n".join([f"Checked {player}: {result}" for player, result in self.seer_checks.items()])
        game_situation = f"{self.get_interwoven_history()}\n\nMy past seer checks:\n{seer_checks_info}"
        
        specific_prompt = """think through your response by answering the following step-by-step:
1. What new information has been revealed in recent conversations?
2. Based on the game history, who seems most suspicious or important to check?
3. How can I use my seer ability most effectively without revealing my role?
4. What information would be most valuable for the village at this point in the game?
5. How can I guide the discussion during the day subtly to help the village? Should I reveal my role at this point?"""

        inner_monologue = self._get_inner_monologue(self.SEER_PROMPT, game_situation, specific_prompt)

        action = self._get_final_action(self.SEER_PROMPT, game_situation, inner_monologue, "choice of player to investigate")

        return action

    def _get_response_for_doctors_save(self, message):
        game_situation = self.get_interwoven_history()
        
        specific_prompt = """think through your response by answering the following step-by-step:
1. Based on recent discussions, who seems to be in the most danger?
2. Have I protected myself recently, or do I need to consider self-protection?
3. Are there any players who might be the Seer or other key roles that I should prioritize?
4. How can I vary my protection pattern to avoid being predictable to the werewolves?
5. How can I contribute to the village discussions with or without revealing my role? Should I reveal my role at this point?"""

        inner_monologue = self._get_inner_monologue(self.DOCTOR_PROMPT, game_situation, specific_prompt)

        action = self._get_final_action(self.DOCTOR_PROMPT, game_situation, inner_monologue, "choice of player to protect")        
        return action

    def _get_discussion_message_or_vote_response_for_common_room(self, message):
        effective_role = self.role
        if effective_role == "wolf":
            effective_role = "villager"
        role_prompt = getattr(self, f"{effective_role.upper()}_PROMPT", self.VILLAGER_PROMPT)
        game_situation = self.get_interwoven_history(include_wolf_channel=False)
        
        specific_prompt = """think through your response by answering the following step-by-step:
1. What important information has been shared in the recent discussions?
2. Based on the game history, who seems most suspicious or trustworthy?
3. What evidence or observations can I share to help the village without revealing my role?
4. How can I guide the discussion in a helpful direction based on what I know?
5. If it's time to vote, who should I vote for and why, considering all the information available?
6. How do I respond if accused during the day without revealing my role?"""

        inner_monologue = self._get_inner_monologue(role_prompt, game_situation, specific_prompt)

        action = self._get_final_action(role_prompt, game_situation, inner_monologue, "vote and discussion point which includes reasoning behind your vote")        
        return action

    def _get_response_for_wolf_channel_to_kill_villagers(self, message):
        if self.role != "wolf":
            return "I am not a werewolf and cannot participate in this channel."
        
        game_situation = self.get_interwoven_history(include_wolf_channel=True)
        
        specific_prompt = """think through your response by answering the following step-by-step:
1. Based on the game history, who are the most dangerous villagers to our werewolf team?
2. Who might be the Seer or Doctor based on their behavior and comments?
3. Which potential target would be least likely to raise suspicion if eliminated?
4. How can we coordinate our actions with other werewolves to maximize our chances of success?
5. Arrive at a consensus for the target and suggest it to the group. Always make suggestions to eliminate at least one person.
6. How can we defend ourselves if accused during the day without revealing our roles?"""

        inner_monologue = self._get_inner_monologue(self.WOLF_PROMPT, game_situation, specific_prompt)

        action = self._get_final_action(self.WOLF_PROMPT, game_situation, inner_monologue, "suggestion for target")        
        return action


# # Testing the agent: Make sure to comment out this code when you want to actually run the agent in some games. 

# # Since we are not using the runner, we need to initialize the agent manually using an internal function:
# from dotenv import load_dotenv
# load_dotenv()
# agent = CoTAgent()
# agent._sentient_llm_config = {
#     "config_list": [{
#             "llm_model_name": os.getenv("SENTIENT_DEFAULT_LLM_MODEL_NAME"), # add model name here, should be: Llama31-70B-Instruct
#             "api_key": os.getenv("MY_UNIQUE_API_KEY"), # add your api key here
#             "llm_base_url": "https://hp3hebj84f.us-west-2.awsapprunner.com"
#         }]  
# }
# agent.__initialize__("Fred", "A werewolf player")
# print(agent._sentient_llm_config)
# agent.role = "wolf"


# # # Simulate receiving and responding to a message
# import asyncio

# async def main():
#     message = ActivityMessage(
#         content_type=MimeType.TEXT_PLAIN,
#         header=ActivityMessageHeader(
#             message_id="456",
#             sender="moderator",
#             channel=GAME_CHANNEL,
#             channel_type=MessageChannelType.GROUP
#         ),
#         content=TextContent(text="Tell me about yourself")
#     )

#     response = await agent.async_respond(message)
#     print(f"Agent response: {response.response.text}")

# asyncio.run(main())
