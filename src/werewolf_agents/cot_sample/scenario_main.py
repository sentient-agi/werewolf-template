# scenario_main.py

SCENARIOS = [
    {
        'name': 'scenario_villager_discussion',
        'description': 'Simulates a villager role discussing during the day.',
        'steps': [
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
            {
                'action': 'notify',
                'message': {
                    'message_id': '2',
                    'sender': 'Alice',
                    'channel': 'GAME_CHANNEL',
                    'channel_type': 'GROUP',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'I think Bob is acting suspicious.',
                },
            },
            {
                'action': 'respond',
                'message_id': '2',
            },
            {
                'action': 'notify',
                'message': {
                    'message_id': '3',
                    'sender': 'MODERATOR',
                    'channel': 'GAME_CHANNEL',
                    'channel_type': 'GROUP',
                    'content_type': 'TEXT_PLAIN',
                    'text': "It's time to vote. Who do you think is the werewolf?",
                },
            },
            {
                'action': 'respond',
                'message_id': '3',
            },
        ],
    },
    {
        'name': 'scenario_seer_night_action',
        'description': "Simulates the seer's night action.",
        'steps': [
            {
                'action': 'notify',
                'message': {
                    'message_id': '4',
                    'sender': 'MODERATOR',
                    'channel': 'direct',
                    'channel_type': 'DIRECT',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'You are the seer.',
                },
            },
            {
                'action': 'respond',
                'message': {
                    'message_id': '5',
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
        'steps': [
            {
                'action': 'notify',
                'message': {
                    'message_id': '6',
                    'sender': 'MODERATOR',
                    'channel': 'direct',
                    'channel_type': 'DIRECT',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'You are the doctor.',
                },
            },
            {
                'action': 'respond',
                'message': {
                    'message_id': '7',
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
        'steps': [
            {
                'action': 'notify',
                'message': {
                    'message_id': '8',
                    'sender': 'MODERATOR',
                    'channel': 'direct',
                    'channel_type': 'DIRECT',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'You are a wolf.',
                },
            },
            {
                'action': 'notify',
                'message': {
                    'message_id': '9',
                    'sender': 'WolfAlice',
                    'channel': 'WOLFS_CHANNEL',
                    'channel_type': 'GROUP',
                    'content_type': 'TEXT_PLAIN',
                    'text': 'Who should we eliminate tonight?',
                },
            },
            {
                'action': 'respond',
                'message_id': '9',
            },
        ],
    },
]
