##################################################################################
# This is file for running multiple games back to back and save to game_results
# Note if you set force_rebuild_agent_image=False, and specify a unique port
# You can run several multirunner.py instances at the same time in dif. terminals
###################################################################################

import os
import json
import time
import argparse
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()

from sentient_campaign.activity_runner.runner import WerewolfCampaignActivityRunner, PlayerAgentConfig

def run_multiple_games(num_games: int, port: int = 8008, results_dir: str = "game_results"):
    # Create results directory if it doesn't exist
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    
    # Create a timestamp-based run ID for this batch of games
    batch_id = int(time.time())
    batch_dir = os.path.join(results_dir, f"batch_{batch_id}")
    Path(batch_dir).mkdir(parents=True, exist_ok=True)
    
    # Ensure transcripts directory exists
    Path("transcripts").mkdir(parents=True, exist_ok=True)
    
    # Store all game results
    all_results = []
    
    for game_num in range(num_games):
        print(f"\nStarting game {game_num + 1} of {num_games}")
        
        # Initialize runner with the specified port
        try:
            runner = WerewolfCampaignActivityRunner(com_server_port=port)
            agent_config = PlayerAgentConfig(
                player_name="James",  # select a name for your agent
                
                #TODO: IMPORTANT!! After building your agent for the first time, you must update this path:
                agent_wheel_path="/Users/aydar/Documents/GitHub/werewolf-template/src/werewolf_agents/simple_sample/dist/simplewolf-0.0.1-py3-none-any.whl",
                module_path="agent/simple_updated.py",
                agent_class_name="SimpleReactiveAgent",
                agent_config_file_path="config.yaml"
            )
            players_sentient_llm_api_keys = [os.getenv("MY_UNIQUE_API_KEY")]

            # Run the game - transcripts will go to the transcripts directory
            game_results = runner.run_locally(
                agent_config,
                players_sentient_llm_api_keys,
                path_to_final_transcript_dump="transcripts",
                force_rebuild_agent_image=False # necessary if you have rebuilt, must turn false if you want to run simultaneously in several terminals
            )
            
            # Save game results in the game_results directory
            results_file = os.path.join(batch_dir, f"game_{game_num + 1}_results_{game_results['activity_id']}.json")
            with open(results_file, 'w') as f:
                json.dump(game_results, f, indent=2)
            
            print(f"Game {game_num + 1} results saved to: {results_file}")
            print(f"Game {game_num + 1} running on port: {port}")
            
            # Add to collection of all results
            all_results.append(game_results)
            
        except Exception as e:
            print(f"Error in game {game_num + 1}: {str(e)}")
            error_info = {
                "game_number": game_num + 1,
                "error": str(e),
                "status": "failed",
                "port": port
            }
            all_results.append(error_info)
    
    # Save summary of all games in the batch directory
    summary_file = os.path.join(batch_dir, f"batch_{batch_id}_summary.json")
    summary = {
        "batch_id": batch_id,
        "total_games": num_games,
        "successful_games": sum(1 for r in all_results if "error" not in r),
        "failed_games": sum(1 for r in all_results if "error" in r),
        "port_used": port,
        "all_games_results": all_results
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nBatch summary saved to: {summary_file}")
    return summary

if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Run multiple werewolf games')
    parser.add_argument('--games', type=int, default=3,
                      help='Number of games to run (default: 3)')
    parser.add_argument('--port', type=int, default=8008,
                      help='Port number for the communication server (default: 8008)')
    
    args = parser.parse_args()
    
    # Run the games with specified parameters
    summary = run_multiple_games(args.games, args.port)
    
    # Print final summary
    print("\nFinal Summary:")
    print(f"Total games run: {summary['total_games']}")
    print(f"Successful games: {summary['successful_games']}")
    print(f"Failed games: {summary['failed_games']}")
    print(f"Port used: {summary['port_used']}") 
