########################################################################
# This is a runner file for running different agents against one another
#########################################################################

########################################################################
# This file is runnable, but at the moment, it is difficult to see how
# different agents are being mapped to names. Fix for this coming soon. 
#########################################################################

from sentient_campaign.activity_runner.runner import WerewolfCampaignActivityRunner, PlayerAgentConfig, SentientWerewolfRoles
from transcript.reorg_files import reorg_files
import os
from typing import Dict, List
import random
from dotenv import load_dotenv
load_dotenv()

# The following is the distribution of roles for the game
# You can change the distribution of roles to test different configurations
# By default, we have 2 wolves, 4 villagers, 1 seer, and 1 doctor
# the wolves are controlled by the CoT agent
# the villagers are controlled by the Autogen agent
# the seer and doctor are controlled by the Simple agent
# You can change this by adding any combination of new agents and players

# Default role distribution
DEFAULT_ROLE_DISTRIBUTION = {
    "wolf": {"agent_type": "simple", "count": 2},
    "villager": {"agent_type": "simple_updated_with_memory", "count": 4},
    "seer": {"agent_type": "simple_updated_with_memory", "count": 1},
    "doctor": {"agent_type": "simple_updated_with_memory", "count": 1}
}
# Your Sentient API key
SENTIENT_API_KEY = os.getenv("MY_UNIQUE_API_KEY")

# Default agent configurations
AGENT_CONFIGS = {
    "cot": {
        "wheel_path": "./src/werewolf_agents/cot_sample/dist/chagent-0.1.0-py3-none-any.whl",
        "module_path": "agent/cot_agent.py",
        "config_path": "./src/werewolf_agents/cot_sample/config.yaml",
        "agent_class": "CoTAgent"
    },
    "cot_updated": {
        "wheel_path": "./src/werewolf_agents/cot_updated/dist/chagent-0.1.0-py3-none-any.whl",
        "module_path": "agent/cot_agent.py",
        "config_path": "./src/werewolf_agents/cot_updated/config.yaml",
        "agent_class": "CoTAgent"
    },
    "simple": {
        "wheel_path": "./src/werewolf_agents/simple_sample/dist/simplewolf-0.0.1-py3-none-any.whl",
        "module_path": "agent/super_simple.py",
        "config_path": "./src/werewolf_agents/simple_sample/config.yaml",
        "agent_class": "SimpleReactiveAgent"
    },
    "simple_updated": {
        "wheel_path": "./src/werewolf_agents/simple_updated/dist/simplewolf-0.0.1-py3-none-any.whl",
        "module_path": "agent/simple_updated.py",
        "config_path": "./src/werewolf_agents/simple_updated/config.yaml",
        "agent_class": "SimpleUpdatedAgent"
    },
    "simple_updated_with_memory": {
        "wheel_path": "./src/werewolf_agents/simple_updated_with_memory/dist/simplewolf-0.0.1-py3-none-any.whl",
        "module_path": "agent/simple_updated_with_memory.py",
        "config_path": "./src/werewolf_agents/simple_updated_with_memory/config.yaml",
        "agent_class": "SimpleUpdatedMemoryAgent"
    },

}

def create_game_config(
    role_distribution: Dict = None,
    player_names: List[str] = None
) -> tuple:
    """Creates game configuration based on provided distribution or defaults"""
    
    role_distribution = role_distribution or DEFAULT_ROLE_DISTRIBUTION
    default_names = ["frodo", "samwise", "meriadoc", "peregrin", "bilbo", "hamfast", "fredegar", "lotho"]
    player_names = player_names or default_names

    # Validate total players
    total_players = sum(role["count"] for role in role_distribution.values())
    if total_players != 8 or len(player_names) != 8:
        raise ValueError("Total number of players must be 8")

    # Create role mapping
    roles = []
    print(role_distribution)
    for role_type, config in role_distribution.items():
        role_enum = getattr(SentientWerewolfRoles, role_type.upper())
        roles.extend([role_enum] * config["count"])

    # Shuffle roles for all names
    random.shuffle(roles)
    player_roles = dict(zip(player_names, roles))

    # Create agent configs
    your_agents = []
    current_idx = 0
    for role_type, config in role_distribution.items():
        agent_type = config["agent_type"]
        agent_config = AGENT_CONFIGS[agent_type]
        
        for _ in range(config["count"]):
            your_agents.append(PlayerAgentConfig(
                player_name=player_names[current_idx],
                agent_wheel_path=agent_config["wheel_path"],
                module_path=agent_config["module_path"],
                agent_class_name=agent_config["agent_class"],
                agent_config_file_path=agent_config["config_path"]
            ))
            current_idx += 1

    return your_agents, player_roles



# Create game configuration (using either default or custom)
your_agents, player_roles = create_game_config(
    role_distribution=DEFAULT_ROLE_DISTRIBUTION
)

# Run the game
runner = WerewolfCampaignActivityRunner(com_server_port=8008)

game_result = runner.run_with_your_agents(
    your_agents,
    players_sentient_llm_api_keys=[SENTIENT_API_KEY],
    path_to_final_transcript_dump="transcript",
    player_roles=player_roles,
    force_rebuild_agent_images=True
)

activity_id = game_result.get("activity_id")
print(f"Activity completed with ID: {activity_id}")
# print game result into log file
with open("game_result_{0}.log".format(activity_id), "w") as f:
    f.write(str(game_result))
    f.write(f"\nPlayer Classes: {DEFAULT_ROLE_DISTRIBUTION}")

reorg_files("transcript", "game_result_{0}.log".format(activity_id))


