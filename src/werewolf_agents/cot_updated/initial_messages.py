# initial_messages.py

def get_initial_messages():
    return [
        {
            'action': 'notify',
            'message': {
                'message_id': 'init1',
                'sender': 'MODERATOR',
                'channel': 'GAME_CHANNEL',
                'channel_type': 'GROUP',
                'content_type': 'TEXT_PLAIN',
                'text': (
                    'Hello players, welcome to the Werewolf game hosted by Sentient! You are playing a fun and commonly played conversational game called Werewolf.\n\n'
                    'I am your moderator, my name is "moderator".\n\n'
                    "You are now part of a game communication group called 'play-arena', where all players can interact. As the moderator, I will use this group to broadcast messages to all players. All players can see messages in this group.\n\n"
                    'Here are the general instructions of this game:\n\n'
                    'Game Instructions:\n\n'
                    '1. Roles:\n'
                    'At the start of each game you will be assigned one of the following roles:\n'
                    '- Villagers: The majority of players. Their goal is to identify and eliminate the werewolves.\n'
                    '- Werewolves: A small group of players who aim to eliminate the villagers.\n'
                    '- Seer: A "special villager" who can learn the true identity of one player each night with help of moderator.\n'
                    '- Doctor: A "special villager" who can protect one person from elimination each night.\n\n'
                    '2. Gameplay:\n'
                    'The game alternates between night and day phases.\n\n'
                    'Night Phase:\n'
                    'a) The moderator announces the start of the night phase and asks everyone to "sleep" (remain inactive).\n'
                    'b) Werewolves\' Turn: Werewolves vote on which player to eliminate in a private communication group with the moderator.\n'
                    'c) Seer\'s Turn: The Seer chooses a player to investigate and learns whether or not this player is a werewolf in a private channel with the moderator.\n'
                    'd) Doctor\'s Turn: The Doctor chooses one player to protect from being eliminated by werewolves in a private channel with the moderator.\n\n'
                    'Day Phase:\n'
                    'a) The moderator announces the end of the night and asks everyone to "wake up" (become active).\n'
                    'b) The moderator reveals if anyone was eliminated during the night.\n'
                    'c) Players discuss and debate who they suspect to be werewolves.\n'
                    'd) Players vote on who to eliminate. The player with the most votes is eliminated and their role is revealed.\n\n'
                    '3. Winning the Game:\n'
                    '- Villagers win if they eliminate all werewolves.\n'
                    '- Werewolves win if they equal or outnumber the villagers.\n\n'
                    '4. Strategy Tips:\n'
                    '- Villagers: Observe player behavior and statements carefully.\n'
                    '- Werewolves: Coordinate during the night and try to blend in during day discussions.\n'
                    '- Seer: Use your knowledge strategically and be cautious about revealing your role.\n'
                    '- Doctor: Protect players wisely and consider keeping your role secret.\n\n'
                    '5. Communication Channels:\n'
                    'a) Main Game Group: "play-arena" - All players can see messages here.\n'
                    'b) Private Messages: You may receive direct messages from the moderator (moderator). These are private messages that only you have access to.\n'
                    'c) Werewolf Group: If you\'re a werewolf, you\'ll have access to a private group wolf\'s-den for night discussions.\n\n'
                    "Here is the list of your fellow players in the game: ['Chagent', 'Michael', 'Helga', 'Ling', 'Haruto', 'Ramesh', 'Jian', 'Ingrid']\n\n"
                    'Remember to engage actively, think strategically, and enjoy the game!'
                ),
            },
        },
        # Additional initial messages common to all scenarios can be added here.
    ]
