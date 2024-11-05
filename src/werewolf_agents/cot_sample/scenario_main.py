# scenario_main.py

from initial_messages import get_initial_messages

SCENARIOS = [
    {
        'name': 'scenario_villager_discussion',
        'description': 'Simulates a villager role discussing during the day.',
        'steps': get_initial_messages() + [
            # Role assignment
            {
                'action': 'notify',
                'message': {
                    'message_id': '1',
                    'sender': 'MODERATOR',
                    'channel': 'direct',
                    'channel_type': 'DIRECT',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'You are a villager.',
                },
            },
            # Night Start
            {
                'action': 'notify',
                'message': {
                    'message_id': '2',
                    'sender': 'MODERATOR',
                    'channel': 'GAME_CHANNEL',
                    'channel_type': 'GROUP',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'Night Start:\n\nHello players, night has started. Please go to sleep.',
                },
            },
            # Day Start
            {
                'action': 'notify',
                'message': {
                    'message_id': '3',
                    'sender': 'MODERATOR',
                    'channel': 'GAME_CHANNEL',
                    'channel_type': 'GROUP',
                    'content_type': 'TEXT_PLAIN',
                    'text': (
                        'Day start:\n\n'
                        'Hello players, Good Morning. Please wake up.\n\n'
                        "Villager dead: Alas! A villager player has been eliminated by the wolves. His name is 'Haruto'.\n\n"
                        "Let me ask one by one about who are the wolves among ourselves."
                    ),
                },
            },
            # Discussion Prompt
            {
                'action': 'notify',
                'message': {
                    'message_id': '4',
                    'sender': 'MODERATOR',
                    'channel': 'GAME_CHANNEL',
                    'channel_type': 'GROUP',
                    'content_type': 'TEXT_PLAIN',
                    'text': "Hey Helga, who do you think is or is not a 'wolf' in the group and what is your reason?",
                },
            },
            # Player Discussion
            {
                'action': 'notify',
                'message': {
                    'message_id': '5',
                    'sender': 'Alice',
                    'channel': 'GAME_CHANNEL',
                    'channel_type': 'GROUP',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'I think Bob is acting suspicious.',
                },
            },
            # Agent's Response to Discussion
            {
                'action': 'respond',
                'message_id': '5',
            },
            # Voting Prompt
            {
                'action': 'notify',
                'message': {
                    'message_id': '6',
                    'sender': 'MODERATOR',
                    'channel': 'GAME_CHANNEL',
                    'channel_type': 'GROUP',
                    'content_type': 'TEXT_PLAIN',
                    'text': "It's time to vote. Who do you think is the werewolf?",
                },
            },
            # Agent's Vote
            {
                'action': 'respond',
                'message_id': '6',
            },
        ],
    },
    {
        'name': 'scenario_seer_night_action',
        'description': "Simulates the seer's night action.",
        'steps': get_initial_messages() + [
            # Role assignment
            {
                'action': 'notify',
                'message': {
                    'message_id': '7',
                    'sender': 'MODERATOR',
                    'channel': 'direct',
                    'channel_type': 'DIRECT',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'You are the seer.',
                },
            },
            # Night Start
            {
                'action': 'notify',
                'message': {
                    'message_id': '8',
                    'sender': 'MODERATOR',
                    'channel': 'GAME_CHANNEL',
                    'channel_type': 'GROUP',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'Night Start:\n\nHello players, night has started. Please go to sleep.',
                },
            },
            # Seer's Turn
            {
                'action': 'respond',
                'message': {
                    'message_id': '9',
                    'sender': 'MODERATOR',
                    'channel': 'direct',
                    'channel_type': 'DIRECT',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'Who would you like to investigate tonight?',
                },
            },
        ],
    },
    {
        'name': 'scenario_doctor_night_action',
        'description': "Simulates the doctor's night action.",
        'steps': get_initial_messages() + [
            # Role assignment
            {
                'action': 'notify',
                'message': {
                    'message_id': '10',
                    'sender': 'MODERATOR',
                    'channel': 'direct',
                    'channel_type': 'DIRECT',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'You are the doctor.',
                },
            },
            # Night Start
            {
                'action': 'notify',
                'message': {
                    'message_id': '11',
                    'sender': 'MODERATOR',
                    'channel': 'GAME_CHANNEL',
                    'channel_type': 'GROUP',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'Night Start:\n\nHello players, night has started. Please go to sleep.',
                },
            },
            # Doctor's Turn
            {
                'action': 'respond',
                'message': {
                    'message_id': '12',
                    'sender': 'MODERATOR',
                    'channel': 'direct',
                    'channel_type': 'DIRECT',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'Who would you like to protect tonight?',
                },
            },
        ],
    },
    {
        'name': 'scenario_wolf_group_action',
        'description': "Simulates the wolf's group discussion.",
        'steps': get_initial_messages() + [
            # Role assignment
            {
                'action': 'notify',
                'message': {
                    'message_id': '13',
                    'sender': 'MODERATOR',
                    'channel': 'direct',
                    'channel_type': 'DIRECT',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'You are a wolf.',
                },
            },
            # Night Start
            {
                'action': 'notify',
                'message': {
                    'message_id': '14',
                    'sender': 'MODERATOR',
                    'channel': 'GAME_CHANNEL',
                    'channel_type': 'GROUP',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'Night Start:\n\nHello players, night has started. Please go to sleep.',
                },
            },
            # Wolf Group Creation
            {
                'action': 'notify',
                'message': {
                    'message_id': '15',
                    'sender': 'MODERATOR',
                    'channel': 'WOLFS_CHANNEL',
                    'channel_type': 'GROUP',
                    'content_type': 'TEXT_PLAIN',
                    'text': (
                        'Wolf night:\n\n'
                        'Hello wolves, I have created this new private group between wolves called "wolfs-group".\n\n'
                        'I will use this group to ask you to vote a player to eliminate every night.\n\n'
                        "Here are the alive villager players for this night: ['Chagent', 'Michael', 'Helga', 'Ling', 'Haruto', 'Jian']"
                    ),
                },
            },
            # Wolf Discussion
            {
                'action': 'notify',
                'message': {
                    'message_id': '16',
                    'sender': 'WolfAlice',
                    'channel': 'WOLFS_CHANNEL',
                    'channel_type': 'GROUP',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'Who should we eliminate tonight?',
                },
            },
            # Agent's Response in Wolf Group
            {
                'action': 'respond',
                'message_id': '16',
            },
        ],
    },
]
