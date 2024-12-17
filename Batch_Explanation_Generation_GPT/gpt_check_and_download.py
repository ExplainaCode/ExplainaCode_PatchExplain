import os
import requests
import json
import pandas as pd
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")

# OpenAI API Constants
API_BASE_URL = "https://api.openai.com/v1"
HEADERS = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

# Paths
batch_id_file = "batch_ids.txt"  # File containing batch IDs
output_csv_path = "../Data/final_batch_results.csv"  # Consolidated CSV file to save results

# Function to check batch status
def get_batch_status(batch_id):
    response = requests.get(f"{API_BASE_URL}/batches/{batch_id}", headers=HEADERS)
    if response.status_code != 200:
        print(f"Error fetching batch status for {batch_id}: {response.json()}")
        return None
    return response.json().get("status"), response.json().get("output_file_id")

# Function to download and process batch output
def download_and_process_batch(batch_id, output_file_id):
    print(f"Downloading results for Batch ID: {batch_id}...")
    
    # Step 1: Download output file content
    output_response = requests.get(
        f"{API_BASE_URL}/files/{output_file_id}/content",
        headers=HEADERS
    )
    if output_response.status_code != 200:
        print(f"Error downloading results for {batch_id}: {output_response.json()}")
        return
    
    # Step 2: Save output to a JSONL file
    output_jsonl_path = f"../Data/batch_output_{batch_id}.jsonl"
    with open(output_jsonl_path, "wb") as f:
        f.write(output_response.content)
    print(f"Results saved to: {output_jsonl_path}")

    # Step 3: Parse JSONL and append results to the final CSV
    explanations = []
    with open(output_jsonl_path, "r") as f:
        for line in f:
            response = json.loads(line)
            custom_id = response.get("custom_id", "N/A")
            explanation = response["choices"][0]["message"]["content"]
            explanations.append({"custom_id": custom_id, "explanation": explanation})

    # Append to CSV file
    df_results = pd.DataFrame(explanations)
    if not os.path.exists(output_csv_path):
        df_results.to_csv(output_csv_path, index=False)
    else:
        df_results.to_csv(output_csv_path, mode='a', header=False, index=False)
    print(f"Results for Batch ID {batch_id} appended to: {output_csv_path}")

# Main function to monitor and download results
def monitor_and_download_results():
    # Load batch IDs from file
    if not os.path.exists(batch_id_file):
        print(f"Batch ID file not found: {batch_id_file}")
        return

    with open(batch_id_file, "r") as f:
        batch_ids = [line.strip() for line in f.readlines()]
    
    print(f"Loaded {len(batch_ids)} batch IDs to monitor.")

    # Monitor each batch and download results
    for batch_id in batch_ids:
        print(f"\nMonitoring Batch ID: {batch_id}")
        while True:
            status, output_file_id = get_batch_status(batch_id)
            if status is None:
                break  # Skip if an error occurs
            
            print(f"Batch ID {batch_id} Status: {status}")
            if status == "completed":
                if output_file_id:
                    download_and_process_batch(batch_id, output_file_id)
                else:
                    print(f"No output file ID found for Batch ID {batch_id}.")
                break
            elif status == "failed":
                print(f"Batch ID {batch_id} failed. Skipping...")
                break
            else:
                time.sleep(60)  # Wait and check again

    print("\nAll batch results have been processed.")

# Run the script
if __name__ == "__main__":
    monitor_and_download_results()
