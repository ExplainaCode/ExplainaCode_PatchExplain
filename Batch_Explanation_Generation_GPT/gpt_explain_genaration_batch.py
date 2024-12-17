import os
import requests
import pandas as pd
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")

# OpenAI API Constants
API_BASE_URL = "https://api.openai.com/v1"
HEADERS = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

# Step 1: Load the DataFrame
print("Loading DataFrame...")
df = pd.read_csv('../Data/1000_record_chunks/1000_chunk_1.csv')  # Adjust the path
sample_size = 100
df = df.sample(sample_size)

# Text file to store batch IDs
batch_id_file = "batch_ids.txt"
open(batch_id_file, "w").close()  # Clear the file before starting

# Function to create JSONL file
def create_jsonl_file(data, batch_number):
    jsonl_file_path = f"../Data/batch_requests_{batch_number}.jsonl"
    with open(jsonl_file_path, "w") as f:
        for index, row in data.iterrows():
            prompt = f"""You are a senior software engineer explaining a bug fix to a junior developer. 
            Your task is to provide a concise explanation of the changes made to fix the bug in the provided code snippets. Follow these guidelines:

            ### Guidelines:
            1. **Bug Identification**: Describe the error in the original code, including its type (e.g., logic error, runtime error) and its impact.
            2. **Problem Analysis**: Explain why the bug is problematic and under what conditions it causes issues.
            3. **Fix Explanation**: Describe the changes in the fixed code and how they address the issue.
            4. **Justification**: Justify why the fix is necessary and how it resolves the problem.
            5. **Improvement Highlight**: Summarize how the fix improves code reliability, functionality, or performance.

            ### Constraints:
            - The explanation must be **concise**, using no more than **100 words**.
            - The explanation should consist of **exactly three sentences**:
            1. Why the buggy code is incorrect.
            2. What changes were made in the fixed code and why they are correct.
            3. How the fixed code improves upon the buggy code.
            - Do not include meta-descriptions such as "This is a three-sentence explanation" or mention word counts in the response.
            - Ensure your explanation aligns with the code context and focuses solely on technical details relevant to the fix.

            ### Example Explanations:

            #### Example 1:
            **Buggy Code:**
            @Override protected void afterTests(){{
                try {{
                    context.shutdown();
                }}
                catch (Exception e) {{
                    throw new RuntimeException("String_Node_Str", e);
                }}
                super.afterTests();
            }}

            **Fixed Code:**
            @Override protected void afterTests(){{
                try {{
                    context.shutdown();
                }}
                catch (Exception e) {{
                    throw new RuntimeException("String_Node_Str", e);
                }}
            }}

            **Explanation:**
            The bug in the original code is the unconditional call to `super.afterTests()`, which executes even if `context.shutdown()` fails, risking inconsistent state. 
            The fixed code removes this call, ensuring `super.afterTests()` is not invoked when an exception occurs, preventing potential errors. 
            This fix ensures predictable cleanup behavior, improving code reliability.

            #### Example 2:
            **Buggy Code:**
            private void updateTreeView(Tree tree){{
                Iterator it = tree.getDepthFirstIterator(false);
                while (it.hasNext()) {{
                    ((Tree<JsonTreeNode>) it.next()).setExpanded(true);
                }}
                editorTreeView.setModel(tree.copy());
            }}

            **Fixed Code:**
            private void updateTreeView(JsonTree tree){{
                JsonTree fixedTree = JsonTreeConverter.serialize(JsonTreeConverter.deserialize(tree));
                Iterator it = fixedTree.getDepthFirstIterator(false);
                while (it.hasNext()) {{
                    ((JsonTree) it.next()).setExpanded(true);
                }}
                editorTreeView.setModel(fixedTree.copy());
            }}

            **Explanation:**
            The original code has a bug where it improperly casts a generic Tree to `Tree<JsonTreeNode>`, which can cause runtime errors if the types don’t match. 
            The fix uses a `JsonTree` with serialization and deserialization to ensure the tree structure is correct and safe to work with. 
            This makes the code more reliable and prevents runtime type errors.
            **Buggy Code:** {row['buggy_code']}
            **Fixed Code:** {row['fixed_code']}
            **Why the fixed code is correct:**"""
            json_obj = {
                "method": "POST",
                "custom_id": f"batch_{batch_number}_record_{index}",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that explains bug fixes clearly."},
                        {"role": "user", "content": prompt}
                    ]
                }
            }
            f.write(json.dumps(json_obj) + "\n")
    return jsonl_file_path

# Function to upload file and create batch job
def process_batch(jsonl_file_path):
    # Step 1: Upload the JSONL file
    with open(jsonl_file_path, "rb") as file:
        upload_response = requests.post(
            f"{API_BASE_URL}/files",
            headers=HEADERS,
            files={"file": file},
            data={"purpose": "batch"}
        )
    if upload_response.status_code != 200:
        print(f"File upload failed: {upload_response.json()}")
        return None
    file_id = upload_response.json()["id"]

    # Step 2: Create a Batch Job
    batch_payload = {
        "input_file_id": file_id,
        "endpoint": "/v1/chat/completions",
        "completion_window": "24h"
    }
    batch_response = requests.post(
        f"{API_BASE_URL}/batches",
        headers=HEADERS,
        json=batch_payload
    )
    if batch_response.status_code != 200:
        print(f"Batch creation failed: {batch_response.json()}")
        return None
    batch_id = batch_response.json()["id"]
    print(f"Batch Job Created: {batch_id}")
    return batch_id

# Step 2: Divide DataFrame into 20-Record Batches
batch_size = 20
num_batches = (len(df) // batch_size) + 1
batch_ids = []

for batch_num in range(num_batches):
    start_idx = batch_num * batch_size
    end_idx = start_idx + batch_size
    chunk = df.iloc[start_idx:end_idx]
    
    if chunk.empty:
        continue

    print(f"\nProcessing Batch {batch_num + 1}...")
    jsonl_path = create_jsonl_file(chunk, batch_num + 1)
    batch_id = process_batch(jsonl_path)

    if batch_id:
        batch_ids.append(batch_id)
        # Append the batch ID to a text file
        with open(batch_id_file, "a") as f:
            f.write(f"{batch_id}\n")
        print(f"Batch {batch_num + 1} Submitted. Batch ID: {batch_id}")
    time.sleep(5)  # Small delay to avoid overwhelming the API

# Step 3: Monitor All Submitted Batch Jobs
print("\nMonitoring Batch Jobs...")
for batch_id in batch_ids:
    print(f"Checking status for Batch ID: {batch_id}")
    while True:
        status_response = requests.get(
            f"{API_BASE_URL}/batches/{batch_id}",
            headers=HEADERS
        )
        if status_response.status_code != 200:
            print(f"Error checking batch status: {status_response.json()}")
            break
        
        status = status_response.json().get("status")
        print(f"Batch {batch_id} Status: {status}")
        if status in ["completed", "failed"]:
            break
        time.sleep(60)  # Check every 60 seconds

print("\nAll Batches Processed!")
print(f"Batch IDs have been saved to {batch_id_file}.")
