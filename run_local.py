import argparse
from sentient_campaign.activity_runner.runner import WerewolfCampaignActivityRunner, PlayerAgentConfig

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run a Werewolf Campaign Activity locally with specified agent configurations.")
    parser.add_argument('--player_name', type=str, required=True, help="Name of the player agent.")
    parser.add_argument('--agent_wheel_path', type=str, required=True, help="Absolute path to the agent wheel file.")
    parser.add_argument('--module_path', type=str, required=True, help="Relative path to the agent file relative to pyproject.toml.")
    parser.add_argument('--agent_class_name', type=str, required=True, help="Class name of IReactiveAgent implementation.")
    parser.add_argument('--agent_config_file_path', type=str, default="", help="Absolute path to the agent config file (can be empty).")
    parser.add_argument('--transcript_dump_path', type=str, default="src/transcripts", help="Path to save the final transcript dump.")
    parser.add_argument('--force_rebuild_agent_image', action='store_true', help="Flag to force rebuild the agent image.")
    
    # Parse arguments
    args = parser.parse_args()

    # Initialize runner and agent config
    runner = WerewolfCampaignActivityRunner()
    agent_config = PlayerAgentConfig(
        player_name=args.player_name,
        agent_wheel_path=args.agent_wheel_path,
        module_path=args.module_path,
        agent_class_name=args.agent_class_name,
        agent_config_file_path=args.agent_config_file_path
    )

    # Placeholder for player API keys
    players_sentient_llm_api_keys = []

    # Run the activity
    activity_id = runner.run_locally(
        agent_config,
        players_sentient_llm_api_keys,
        path_to_final_transcript_dump=args.transcript_dump_path,
        force_rebuild_agent_image=args.force_rebuild_agent_image
    )

    print(f"Activity ID: {activity_id}")

if __name__ == "__main__":
    main()
