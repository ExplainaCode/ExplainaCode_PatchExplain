import os
import json
import requests
from dotenv import load_dotenv

# Load OpenAI API Key
load_dotenv()
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")

# API Configuration
API_BASE_URL = "https://api.openai.com/v1"
HEADERS = {"Authorization": f"Bearer {OPEN_AI_API_KEY}"}

# File Paths
batch_ids_file = "batch_ids.txt"  # Text file containing batch IDs
errors_log_file = "errors_log.json"  # File to store errors

# Function to check a batch's status
def check_batch_status(batch_id):
    response = requests.get(
        f"{API_BASE_URL}/batches/{batch_id}",
        headers=HEADERS
    )
    if response.status_code == 200:
        batch_details = response.json()
        return batch_details
    else:
        print(f"Failed to retrieve details for Batch ID: {batch_id}")
        return {"error": response.json()}

# Function to process errors and save to log
def process_errors(batch_details, batch_id, error_log):
    if "errors" in batch_details and batch_details["errors"]["data"]:
        print(f"\nErrors found in Batch ID: {batch_id}")
        error_data = batch_details["errors"]["data"]
        for error in error_data:
            print(f"Line {error.get('line', 'N/A')}: {error.get('message', 'No message')}")
        error_log[batch_id] = error_data
    else:
        print(f"Batch ID {batch_id} has no errors.")

# Main Script Execution
def main():
    # Check if batch_ids.txt exists
    if not os.path.exists(batch_ids_file):
        print(f"File not found: {batch_ids_file}")
        return

    # Read all batch IDs
    with open(batch_ids_file, "r") as f:
        batch_ids = [line.strip() for line in f.readlines()]
    
    print(f"Loaded {len(batch_ids)} batch IDs to check.\n")

    # Error log dictionary
    error_log = {}

    # Process each batch
    for batch_id in batch_ids:
        print(f"Checking Batch ID: {batch_id}...")
        batch_details = check_batch_status(batch_id)

        # If status is completed, display info
        if batch_details.get("status") == "completed":
            print(f"Batch ID {batch_id} completed successfully.\n")
        elif batch_details.get("status") == "failed":
            print(f"Batch ID {batch_id} has failed. Checking errors...")
            process_errors(batch_details, batch_id, error_log)
        else:
            print(f"Batch ID {batch_id} is in progress. Current status: {batch_details.get('status')}\n")
    
    # Save errors to log file if any
    if error_log:
        with open(errors_log_file, "w") as f:
            json.dump(error_log, f, indent=4)
        print(f"\nErrors have been saved to: {errors_log_file}")
    else:
        print("\nNo errors found in any batch jobs.")

if __name__ == "__main__":
    main()
