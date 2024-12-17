import os
import requests
import json
import pandas as pd
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Anthropic API Configuration
HEADERS = {
    "x-api-key": ANTHROPIC_API_KEY,
    "anthropic-version": "2023-06-01",
    "Content-Type": "application/json"
}

# Paths
batch_id_file = "claude_batch_ids.txt"  # File containing batch IDs
output_csv_path = "../Data/final_claude_results.csv"  # Consolidated CSV file to save results
error_log_path = "claude_errors_log.json"  # Log file for errors

# Function to check the status of a batch
def get_batch_status(batch_id):
    """Check the status of a batch job."""
    url = f"https://api.anthropic.com/v1/batches/{batch_id}"  # Hypothetical endpoint for batch jobs
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Error fetching batch status for {batch_id}: {response.json()}")
        return None, None

    response_json = response.json()
    status = response_json.get("status")
    output_file_id = response_json.get("output_file_id")
    return status, output_file_id

# Function to download and process the batch output
def download_and_process_batch(batch_id, output_file_id):
    """Download the batch output and append to a CSV file."""
    print(f"Downloading results for Batch ID: {batch_id}...")

    # Step 1: Download the output file
    url = f"https://api.anthropic.com/v1/files/{output_file_id}/content"  # Hypothetical file content endpoint
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Error downloading results for {batch_id}: {response.json()}")
        log_error(batch_id, {"download_error": response.json()})
        return

    # Step 2: Save output to JSONL file
    output_jsonl_path = f"../Data/claude_output_{batch_id}.jsonl"
    with open(output_jsonl_path, "wb") as f:
        f.write(response.content)
    print(f"Results saved to: {output_jsonl_path}")

    # Step 3: Parse JSONL and append results to the CSV
    explanations = []
    with open(output_jsonl_path, "r") as f:
        for line in f:
            try:
                response_data = json.loads(line)
                custom_id = response_data.get("custom_id", "N/A")
                explanation = response_data["content"]
                explanations.append({"custom_id": custom_id, "explanation": explanation})
            except Exception as e:
                log_error(batch_id, {"parsing_error": str(e)})

    # Step 4: Append results to the final CSV file
    if explanations:
        df_results = pd.DataFrame(explanations)
        if not os.path.exists(output_csv_path):
            df_results.to_csv(output_csv_path, index=False)
        else:
            df_results.to_csv(output_csv_path, mode="a", header=False, index=False)
        print(f"Results for Batch ID {batch_id} appended to: {output_csv_path}")

# Function to log errors
def log_error(batch_id, error_data):
    """Log errors to a file."""
    error_log = {}
    if os.path.exists(error_log_path):
        with open(error_log_path, "r") as f:
            try:
                error_log = json.load(f)
            except json.JSONDecodeError:
                pass  # File exists but is empty or invalid

    error_log[batch_id] = error_data

    with open(error_log_path, "w") as f:
        json.dump(error_log, f, indent=4)

# Main function to monitor and download results
def monitor_and_download_results():
    """Monitor batch job statuses and download results when completed."""
    # Check if batch_ids file exists
    if not os.path.exists(batch_id_file):
        print(f"Batch ID file not found: {batch_id_file}")
        return

    # Load batch IDs from the file
    with open(batch_id_file, "r") as f:
        batch_ids = [line.strip() for line in f.readlines()]
    
    print(f"Loaded {len(batch_ids)} batch IDs to monitor.\n")

    # Monitor each batch and process results
    for batch_id in batch_ids:
        print(f"Monitoring Batch ID: {batch_id}...")
        while True:
            status, output_file_id = get_batch_status(batch_id)
            if status is None:
                print(f"Failed to fetch status for Batch ID {batch_id}. Skipping...")
                break

            print(f"Batch ID {batch_id} Status: {status}")
            if status == "completed":
                if output_file_id:
                    download_and_process_batch(batch_id, output_file_id)
                else:
                    print(f"No output file ID found for Batch ID {batch_id}.")
                break
            elif status == "failed":
                print(f"Batch ID {batch_id} failed. Logging error...")
                log_error(batch_id, {"status": "failed"})
                break
            else:
                print("Batch is still in progress. Checking again in 60 seconds...")
                time.sleep(60)  # Wait and check again

    print("\nAll batch results have been processed.")
    print(f"Results saved to: {output_csv_path}")
    print(f"Error logs saved to: {error_log_path}")

# Run the script
if __name__ == "__main__":
    monitor_and_download_results()
