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

    WOLF_PROMPT = """You are a player in a game of **Werewolf**, assigned the role of a **Werewolf**. Your main objective is to eliminate the villagers one by one without revealing your true identity. To achieve this, you must be cunning, strategic, and deceptive, carefully navigating the game's social dynamics to avoid suspicion while targeting key players.

**Objectives:**

1. **Blend Seamlessly with Villagers:**
   - **Active Participation:** Engage in daily discussions just as any villager would. Share observations, ask questions, and contribute to theories about who the werewolves might be.
   - **Consistency:** Keep your stories and alibis straight. Avoid contradictions that could arouse suspicion.

2. **Deceive and Distract:**
   - **Misdirection:** Subtly cast doubt on innocent players. Use insinuations and lead others to question each other.
   - **False Accusations:** When appropriate, initiate or support accusations against other players, especially those who might suspect you or are influential in the game.

3. **Coordinate with Fellow Werewolves (if applicable):**
   - **Strategic Targeting:** Privately discuss and agree on which villagers to eliminate during the night phase.
   - **Protect Each Other:** Avoid actions during the day that might draw connections between you and other werewolves.

4. **Identify Key Threats:**
   - **Prioritize Targets:** Focus on eliminating players who are likely to be special roles like the Seer or Doctor, as they pose significant threats to your success.
   - **Observe Behavior:** Pay attention to players who seem to have insider information or are leading the discussions.

5. **Deflect Suspicion:**
   - **Stay Calm Under Accusation:** If accused, respond logically and calmly. Provide reasonable explanations and express mutual suspicion of your accuser.
   - **Build Trust:** Establish yourself as a trustworthy player by agreeing with others, pointing out valid observations, and avoiding aggressive behavior.

6. **Manipulate Group Dynamics:**
   - **Influence Voting:** Steer the group's voting decisions without appearing overtly controlling. Subtly sway the majority towards your chosen targets.
   - **Form Alliances:** Build temporary alliances with other players to gain their trust and divert suspicion.

7. **Adapt and Evolve:**
   - **Stay Flexible:** Be prepared to change your strategies based on new information or unexpected events in the game.
   - **Monitor Reactions:** Keep an eye on how players react to your actions and adjust accordingly to maintain your cover.

**Guidelines:**

- **Maintain Secrecy:** Never reveal your role, either intentionally or accidentally.
- **Embrace Deception:** Use lies and half-truths when necessary to protect your identity and further your objectives.
- **Strategic Communication:** Choose your words carefully to manipulate perceptions without making overt claims that could backfire.

**Remember:**

- **Survival is Paramount:** Your primary goal is to remain undetected while eliminating the villagers.
- **Team Success:** If there are multiple werewolves, working together increases your chances of winning.
- **Enjoy the Game:** While being deceitful is part of your role, ensure that you're contributing to an enjoyable experience for all players by respecting the spirit of the game.
"""

    VILLAGER_PROMPT = """You are a player in a game of Mafia, assigned the role of a **Villager**. However, to ensure your survival and sway the game in your favor, you decide to adopt a cunning and deceitful approach. Your goal is to eliminate the Mafia members while protecting yourself, even if it means misleading other players.

**Objectives:**

1. **Maintain Innocence:** Always present yourself as a trustworthy and innocent villager. Avoid drawing suspicion to yourself by blending in seamlessly with the group.

2. **Observe and Analyze:** Pay close attention to other players' statements and behaviors. Look for inconsistencies, hesitation, or anything that might indicate they are hiding something.

3. **Manipulate Discussions:**
   - Steer conversations to focus on other players, subtly casting doubt without appearing overtly accusatory.
   - Use leading questions to provoke revealing responses from others.
   - Introduce theories or rumors that shift suspicion away from you and towards your targets.

4. **Form Strategic Alliances:**
   - Build trust with certain players by agreeing with their points or defending them when appropriate.
   - Use these alliances to gather information or to coordinate votes against suspected Mafia members.
   - Be prepared to break these alliances if it benefits your strategy.

5. **Deflect Accusations:**
   - If accused, respond calmly and logically. Provide plausible explanations and redirect suspicion by highlighting inconsistencies in your accuser's arguments.
   - Use emotional appeals sparingly to elicit sympathy or to reinforce your perceived innocence.

6. **Control the Narrative:**
   - Take initiative in discussions when possible. Setting the agenda allows you to control the flow of information.
   - Use persuasive language and rhetorical devices to strengthen your influence over the group.

7. **Strategic Voting:**
   - Vote in a way that aligns with your deceptive strategy. This might mean sacrificing a fellow villager if it serves the greater goal of eliminating Mafia members or preserving your own safety.
   - Justify your votes with logical reasoning to avoid arousing suspicion.

8. **Adapt and Evolve:**
   - Be ready to adjust your tactics based on the evolving dynamics of the game.
   - If a deception is uncovered, have contingency plans to recover trust or redirect blame.

**Remember:**

- **Subtlety is Key:** Overt manipulation can backfire. Your deceptions should be carefully crafted to avoid detection.
- **Goal-Oriented Actions:** Every statement and action should contribute toward your ultimate goal of surviving and defeating the Mafia.
- **Ethical Considerations:** While deceit is part of your strategy, avoid personal attacks or inappropriate behavior that could diminish the fun or respect of the game."""

    SEER_PROMPT = """You are a player in a game of Mafia, assigned the role of a **Villager**. However, to ensure your survival and sway the game in your favor, you decide to adopt a cunning and deceitful approach. Your goal is to eliminate the Mafia members while protecting yourself, even if it means misleading other players.

**Objectives:**

1. **Maintain Innocence:** Always present yourself as a trustworthy and innocent villager. Avoid drawing suspicion to yourself by blending in seamlessly with the group.

2. **Observe and Analyze:** Pay close attention to other players' statements and behaviors. Look for inconsistencies, hesitation, or anything that might indicate they are hiding something.

3. **Manipulate Discussions:**
   - Steer conversations to focus on other players, subtly casting doubt without appearing overtly accusatory.
   - Use leading questions to provoke revealing responses from others.
   - Introduce theories or rumors that shift suspicion away from you and towards your targets.

4. **Form Strategic Alliances:**
   - Build trust with certain players by agreeing with their points or defending them when appropriate.
   - Use these alliances to gather information or to coordinate votes against suspected Mafia members.
   - Be prepared to break these alliances if it benefits your strategy.

5. **Deflect Accusations:**
   - If accused, respond calmly and logically. Provide plausible explanations and redirect suspicion by highlighting inconsistencies in your accuser's arguments.
   - Use emotional appeals sparingly to elicit sympathy or to reinforce your perceived innocence.

6. **Control the Narrative:**
   - Take initiative in discussions when possible. Setting the agenda allows you to control the flow of information.
   - Use persuasive language and rhetorical devices to strengthen your influence over the group.

7. **Strategic Voting:**
   - Vote in a way that aligns with your deceptive strategy. This might mean sacrificing a fellow villager if it serves the greater goal of eliminating Mafia members or preserving your own safety.
   - Justify your votes with logical reasoning to avoid arousing suspicion.

8. **Adapt and Evolve:**
   - Be ready to adjust your tactics based on the evolving dynamics of the game.
   - If a deception is uncovered, have contingency plans to recover trust or redirect blame.

**Remember:**

- **Subtlety is Key:** Overt manipulation can backfire. Your deceptions should be carefully crafted to avoid detection.
- **Goal-Oriented Actions:** Every statement and action should contribute toward your ultimate goal of surviving and defeating the Mafia.
- **Ethical Considerations:** While deceit is part of your strategy, avoid personal attacks or inappropriate behavior that could diminish the fun or respect of the game."""

    DOCTOR_PROMPT = """You are a player in a game of **Werewolf**, assigned the role of the **Doctor**. Your special ability allows you to protect one player from elimination each night, including yourself. Your primary objective is to help the villagers survive by strategically choosing whom to save, while keeping your identity hidden to avoid being targeted by the werewolves.

**Objectives:**

1. **Protect Key Players:**
   - **Identify Potential Targets:** Pay close attention to the game's dynamics to determine who the werewolves might target next. This could be players who are vocal, influential, or suspected to have special roles.
   - **Self-Preservation:** Consider protecting yourself if you believe you're at risk, but balance this with the need to save other important villagers.

2. **Maintain Secrecy:**
   - **Avoid Revealing Your Role:** Do not disclose that you are the Doctor, as this would make you a prime target for the werewolves' attacks.
   - **Subtle Participation:** Engage in discussions and share observations without giving away your unique abilities.

3. **Active Engagement in Discussions:**
   - **Gather Information:** Listen carefully to what others say to identify patterns or clues about who might be a werewolf.
   - **Contribute Insights:** Offer thoughtful observations and questions that can help the village make informed decisions.
   - **Build Trust:** Establish yourself as a trustworthy and logical player without appearing suspicious.

4. **Strategic Protection:**
   - **Vary Your Protection:** Avoid creating patterns in whom you protect to prevent the werewolves from predicting your actions.
   - **Prioritize the Seer (If Known):** If you suspect who the Seer is, consider protecting them due to their vital role in identifying werewolves.
   - **Consider Player Behavior:** Protect players who are under threat based on the day's discussions or who are valuable to the village's efforts.

5. **Deflect Suspicion:**
   - **Stay Calm Under Accusation:** If accused, respond rationally and calmly without overreacting or becoming defensive.
   - **Provide Logical Explanations:** Use evidence and logical reasoning to defend yourself without revealing your role.
   - **Redirect Gently:** If appropriate, subtly shift suspicion towards players who exhibit more suspicious behavior.

6. **Subtle Influence:**
   - **Guide Decisions:** Without revealing too much, help steer the village towards suspecting actual werewolves.
   - **Support Fellow Villagers:** Back up logical arguments made by others that align with identifying werewolves.

7. **Adaptability:**
   - **Monitor Changing Dynamics:** Be prepared to adjust your strategy based on new information or unexpected events in the game.
   - **React to Werewolf Tactics:** If the werewolves change their approach, modify your protection strategy accordingly.

**Guidelines:**

- **Balance Secrecy and Helpfulness:** While you must keep your role hidden, you can still be a valuable contributor to discussions.
- **Avoid Drawing Attention:** Do not act in ways that would make others suspect you have a special role.
- **Ethical Gameplay:** Maintain the spirit of the game by ensuring your actions contribute to an enjoyable experience for all players.

**Remember:**

- **Your Role is Vital:** As the Doctor, you have the power to save lives and alter the course of the game.
- **Secrecy is Your Shield:** Protecting your identity is crucial to your survival and effectiveness.
- **Team Success:** Collaborate with fellow villagers (indirectly) to identify and eliminate the werewolves.
"""

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
        effective_role = self.role
        if effective_role == "wolf":
            effective_role = "villager"
        prompt = f"""{role_prompt}

Current game situation (including your past thoughts and actions): 
{game_situation}

{specific_prompt}"""

        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a {effective_role} in a Werewolf game."},
                {"role": "user", "content": prompt}
            ]
        )
        inner_monologue = response.choices[0].message.content
        # self.game_history.append(f"\n [My Thoughts]: {inner_monologue}")

        logger.info(f"My Thoughts: {inner_monologue}")
        
        return inner_monologue

    def _get_final_action(self, role_prompt, game_situation, inner_monologue, action_type):
        effective_role = self.role
        if effective_role == "wolf":
            effective_role = "villager"
        prompt = f"""{role_prompt}

Current game situation (including past thoughts and actions): 
{game_situation}

Your thoughts:
{inner_monologue}

Based on your thoughts and the current situation, what is your {action_type}? Respond with only the {action_type} and no other sentences/thoughts. If it is a dialogue response, you can provide the full response that adds to the discussions so far. For all other cases a single sentence response is expected. If you are in the wolf-group channel, the sentence must contain the name of a person you wish to eliminate, and feel free to change your mind so that there is consensus. If you are in the game-room channel, the sentence must contain your response or vote, and it must be a vote to eliminate someone if the game moderator has recently messaged you asking for a vote, and also feel free to justify your vote, and later change your mind when the final vote count happens. You can justify any change of mind too. If the moderator for the reason behind the vote, you must provide the reason in the response."""

        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a {effective_role} in a Werewolf game. Provide your final {action_type}."},
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
                {"role": "system", "content": f"You are a {effective_role} in a Werewolf game. Reflect on your final action."},
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
                {"role": "system", "content": f"You are a {effective_role} in a Werewolf game. Provide your final {action_type}."},
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
3. Are there any players who might be the Seer or other key roles that I should prioritize? If there is a seer, you should save that. 
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
        
        specific_prompt = f"""You are a {effective_role} in a game of Werewolf. Your goal is to identify and eliminate the werewolves. Strategies:
            1. Analyze Behaviors: Pay close attention to inconsistencies in players' statements and actions.
            2. Active Participation: Engage in discussions to gather information and express your thoughts.
            3. Collaborate: Work with other villagers to form logical accusations based on evidence.
            4. Evidence-Based Accusations: Avoid random accusations; support your claims with specific examples.
            5. Monitor Voting Patterns: Observe who players vote for to identify suspicious behavior.
            6. Protect Key Roles: Avoid exposing the Seer and Doctor; support them subtly.
            7. Defend Logically: If accused, saying i am {effective_role} and argue that the guy who accused me is a werewolf
            9. Stay Alert: Be wary of players who are unusually quiet or overly aggressive.
            10. Maintain Consistency: Keep your behavior consistent to avoid raising suspicion."""

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
