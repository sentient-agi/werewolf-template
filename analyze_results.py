import os
import ast
from datetime import datetime


def get_last_n_folders(transcript_dir, n=8):
    # Get a list of all subdirectories in the transcript directory
    folders = [os.path.join(transcript_dir, d) for d in os.listdir(transcript_dir)
               if os.path.isdir(os.path.join(transcript_dir, d))]
    # Sort the folders by modification time (newest last)
    folders.sort(key=os.path.getmtime)
    # Return the last n folders
    return folders[-n:]


def parse_game_result(game_result_path):
    with open(game_result_path, 'r') as file:
        lines = file.readlines()
        if len(lines) < 2:
            print(f"Unexpected format in {game_result_path}")
            return None, None
        # First line is the game result dictionary
        game_result_line = lines[0].strip()
        # Second line starts with 'Player Classes: {dictionary}'
        player_classes_line = lines[1].strip()
        if player_classes_line.startswith('Player Classes:'):
            player_classes_str = player_classes_line[len('Player Classes:'):].strip()
        else:
            print(f"Unexpected format in {game_result_path}")
            return None, None

        # Parse both dictionaries safely using ast.literal_eval
        try:
            game_result = ast.literal_eval(game_result_line)
            player_classes = ast.literal_eval(player_classes_str)
        except Exception as e:
            print(f"Error parsing file {game_result_path}: {e}")
            return None, None

        return game_result, player_classes


def determine_runner(player_classes):
    if (player_classes.get('wolf', {}).get('agent_type') == 'simple_updated_with_memory_and_cot' and
            player_classes.get('villager', {}).get('agent_type') == 'simple_updated_with_memory'):
        return 'A'
    elif (player_classes.get('wolf', {}).get('agent_type') == 'simple_updated_with_memory' and
          player_classes.get('villager', {}).get('agent_type') == 'simple_updated_with_memory_and_cot'):
        return 'B'
    else:
        return 'Unknown'


def generate_report(transcript_dir):
    last_eight_folders = get_last_n_folders(transcript_dir, n=8)
    report_lines = []
    summary_stats = {'A': {'VILLAGERS': 0, 'WOLVES': 0}, 'B': {'VILLAGERS': 0, 'WOLVES': 0}}

    for folder in last_eight_folders:
        # Look for the game_result*.log file in the folder
        game_result_files = [f for f in os.listdir(folder) if f.startswith('game_result') and f.endswith('.log')]
        if not game_result_files:
            print(f"No game result file found in {folder}")
            continue
        # Assume there's only one game_result file per folder
        game_result_path = os.path.join(folder, game_result_files[0])
        game_result, player_classes = parse_game_result(game_result_path)
        if game_result is None or player_classes is None:
            continue
        runner = determine_runner(player_classes)
        winner = game_result.get('success_game_stats', {}).get('winner', 'Unknown')
        game_id = game_result.get('activity_id', 'Unknown')
        players = game_result.get('players', [])
        player_roles = game_result.get('player_roles', {})
        agent_types = {}
        for role, info in player_classes.items():
            agent_type = info.get('agent_type', 'Unknown')
            agent_types[role] = agent_type

        report_lines.append(f"Game ID: {game_id}")
        report_lines.append(f"Runner: {runner}")
        report_lines.append(f"Winner: {winner}")
        report_lines.append("Players and Roles:")
        for player in players:
            role = player_roles.get(player, 'Unknown')
            agent_type = agent_types.get(role, 'Unknown')
            report_lines.append(f" - {player}: {role} (Agent Type: {agent_type})")
        report_lines.append("\n")

        # Update summary statistics
        if runner in summary_stats:
            if winner in summary_stats[runner]:
                summary_stats[runner][winner] += 1

    # Add summary statistics to the report
    report_lines.append("Summary Statistics:")
    for runner, stats in summary_stats.items():
        report_lines.append(f"Runner {runner}:")
        for winner, count in stats.items():
            report_lines.append(f" - {winner} wins: {count}")
        report_lines.append("\n")

    # Save the report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join('t_results', f"versus_summary_{timestamp}.log")
    with open(output_file, 'w') as out_file:
        out_file.write('\n'.join(report_lines))

    print(f"Report generated and saved to {output_file}")


if __name__ == "__main__":
    transcript_directory = "transcript"  # Replace with the path to your transcript directory
    generate_report(transcript_directory)
