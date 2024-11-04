# test_runner.py

import asyncio
import logging
import os
from agent.cot_agent import CoTAgent
from dotenv import load_dotenv
from scenario_main import SCENARIOS
from datetime import datetime

# Import necessary classes
from sentient_campaign.agents.v1.message import (
    ActivityMessageHeader,
    MessageChannelType,
    MimeType,
    TextContent,
)

load_dotenv()

# Set up logging (optional)
logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger("test_runner")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

def agent_factory():
    """Creates and initializes a new agent instance."""
    agent = CoTAgent()
    agent._sentient_llm_config = {
        "config_list": [
            {
                "llm_model_name": os.getenv("SENTIENT_DEFAULT_LLM_MODEL_NAME"),
                "api_key": os.getenv("MY_UNIQUE_API_KEY"),
                "llm_base_url": os.getenv("SENTIENT_DEFAULT_LLM_BASE_URL"),
            }
        ]
    }
    agent.__initialize__("Fred", "A werewolf player")
    return agent

async def run_scenario(agent_factory, scenario_function):
    """Runs a given scenario using a new agent instance."""
    agent = agent_factory()
    output = []

    # Capture the print statements in a list
    import sys
    from io import StringIO

    original_stdout = sys.stdout
    sys.stdout = capture = StringIO()

    try:
        await scenario_function(agent)
    except Exception as e:
        print(f"Error during scenario execution: {e}")

    # Restore original stdout
    sys.stdout = original_stdout

    return capture.getvalue()

async def main():
    """Main function to run all scenarios and save results to HTML."""
    results = []
    for scenario in SCENARIOS:
        logger.info(f"Running scenario: {scenario.__name__}")
        output = await run_scenario(agent_factory, scenario)
        results.append({
            'scenario': scenario.__name__,
            'description': scenario.__doc__,
            'output': output,
        })

    # Generate HTML report
    generate_html_report(results)

def generate_html_report(results):
    """Generates an HTML report from the test results."""
    html_content = """
    <html>
    <head>
        <title>Scenario Test Results</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            h2 { color: #555; }
            p { color: #777; }
            pre { background-color: #f4f4f4; padding: 10px; border-radius: 5px; }
            .scenario { margin-bottom: 40px; }
        </style>
    </head>
    <body>
    """
    html_content += f"<h1>Scenario Test Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h1>"
    for result in results:
        html_content += f"""
        <div class="scenario">
            <h2>{result['scenario']}</h2>
            <p>{result['description']}</p>
            <pre>{result['output']}</pre>
        </div>
        """
    html_content += "</body></html>"

    with open("scenario_main.html", "w") as f:
        f.write(html_content)
    print("Test results saved to scenario_main.html")

if __name__ == "__main__":
    asyncio.run(main())
