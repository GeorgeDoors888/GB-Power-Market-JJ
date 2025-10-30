import os
import subprocess
import sys

from flask import Flask, jsonify
from flask_cors import CORS

# --- Configuration ---
# Get the absolute path of the virtual environment's Python executable
# This ensures we use the same environment the project is set up with.
VENV_PYTHON_PATH = os.path.join(os.path.dirname(sys.executable), "python")
# Get the absolute path of the directory where the scripts are located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing


def run_script(script_name, args=[]):
    """
    A helper function to securely run our existing analysis scripts
    in a subprocess, ensuring they use the correct virtual environment.
    """
    try:
        # Construct the full command
        script_path = os.path.join(SCRIPT_DIR, script_name)
        command = [VENV_PYTHON_PATH, script_path] + args

        # Set the necessary environment variable for GCP authentication
        env = os.environ.copy()
        env["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.expanduser(
            "~/.config/gcloud/application_default_credentials.json"
        )

        print(f"Running command: {' '.join(command)}")

        # Execute the command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,  # This will raise an exception if the script fails
            cwd=SCRIPT_DIR,
            env=env,
        )

        print("Script output:", result.stdout)
        return {"status": "success", "output": result.stdout}

    except subprocess.CalledProcessError as e:
        # If the script returns a non-zero exit code, it's an error
        print(f"Error running {script_name}: {e.stderr}")
        return {"status": "error", "message": e.stderr}
    except Exception as e:
        # Catch any other exceptions
        print(f"An unexpected error occurred: {str(e)}")
        return {"status": "error", "message": str(e)}


# --- API Routes ---


@app.route("/")
def index():
    """A simple route to check if the server is running."""
    return "Web API server is running. Ready to receive requests from Google Sheets."


@app.route("/run/ingest-latest", methods=["POST", "GET"])
def run_ingest_latest():
    """
    API endpoint to run the main data ingestion script for the last few hours.
    """
    print("Received request to run latest data ingestion...")
    # Ingest data for the last 8 hours
    return jsonify(run_script("ingest_elexon_fixed.py", ["--hours", "8"]))


@app.route("/run/wind-forecast-analysis", methods=["POST", "GET"])
def run_wind_analysis():
    """
    API endpoint to run the wind forecast accuracy analysis.
    """
    print("Received request to run wind forecast analysis...")
    return jsonify(run_script("wind_forecast_analyzer.py"))


@app.route("/run/battery-opportunity-analysis", methods=["POST", "GET"])
def run_battery_analysis():
    """
    API endpoint to run the battery opportunity analysis.
    """
    print("Received request to run battery opportunity analysis...")
    return jsonify(run_script("battery_opportunity_analyzer.py"))


# --- Main Execution ---

if __name__ == "__main__":
    # Runs the Flask server on localhost, port 5001
    # You can access it at http://127.0.0.1:5001
    print("Starting Flask server...")
    app.run(host="127.0.0.1", port=5001, debug=True)
