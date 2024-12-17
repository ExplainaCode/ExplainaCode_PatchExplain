import os
import requests
import pandas as pd
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Anthropic API Constants
API_BASE_URL = "https://api.anthropic.com/v1/messages"  # Claude API endpoint
HEADERS = {
    "x-api-key": ANTHROPIC_API_KEY,
    "anthropic-version": "2023-06-01",
    "Content-Type": "application/json"
}

# Step 1: Load the DataFrame
print("Loading DataFrame...")
df = pd.read_csv('../Data/evaluations/100_record_eval_only_gpt_4-0_mini.csv')  # Adjust the path
sample_size = 100
df = df.sample(sample_size)

# Text file to store batch IDs and errors
batch_id_file = "claude_batch_ids.txt"
error_log_file = "claude_errors_log.json"
open(batch_id_file, "w").close()  # Clear the batch ID file
open(error_log_file, "w").close()  # Clear the error log file

# Function to create JSONL file
def create_jsonl_file(data, batch_number):
    jsonl_file_path = f"../Data/claude_requests_batch_{batch_number}.jsonl"
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
                "url": "/v1/messages",
                "body": {
                    "model": "claude-3-5-haiku-latest",
                    "max_tokens": 200,
                    "temperature": 0.5,
                    "messages": [{"role": "user", "content": prompt}]
                }
            }
            f.write(json.dumps(json_obj) + "\n")
    return jsonl_file_path

# Function to process each record and collect responses
def process_batch(data, batch_number):
    print(f"Processing Batch {batch_number}...")
    results = []
    errors = {}

    for index, row in data.iterrows():
        try:
            # Construct the API payload
            payload = {
                "model": "claude-3-5-haiku-latest",
                "max_tokens": 200,
                "temperature": 0.5,
                "messages": [{"role": "user", "content": f"""
                You are a senior software engineer explaining a bug fix to a junior developer.
                **Buggy Code:** {row['buggy_code']}
                **Fixed Code:** {row['fixed_code']}
                **Why the fixed code is correct:**"""}]
            }

            # Send request to the Anthropic Claude API
            response = requests.post(API_BASE_URL, headers=HEADERS, json=payload)
            response_json = response.json()

            if response.status_code == 200 and "content" in response_json:
                explanation = response_json['content']
                results.append({"custom_id": f"batch_{batch_number}_record_{index}", "explanation": explanation})
            else:
                errors[f"batch_{batch_number}_record_{index}"] = response_json

        except Exception as e:
            errors[f"batch_{batch_number}_record_{index}"] = str(e)
        
        time.sleep(1)  # Delay to avoid rate limiting

    # Save errors, if any
    if errors:
        with open(error_log_file, "a") as f:
            json.dump(errors, f, indent=4)
    return results

# Step 2: Divide DataFrame into 20-Record Batches
batch_size = 20
num_batches = (len(df) // batch_size) + 1
all_results = []

for batch_num in range(num_batches):
    start_idx = batch_num * batch_size
    end_idx = start_idx + batch_size
    chunk = df.iloc[start_idx:end_idx]

    if chunk.empty:
        continue

    # Process the batch and collect results
    batch_results = process_batch(chunk, batch_num + 1)
    all_results.extend(batch_results)

    # Save batch ID
    with open(batch_id_file, "a") as f:
        f.write(f"claude_batch_{batch_num + 1}\n")

# Step 3: Save Results to CSV
output_csv_path = "../Data/evaluations/final_claude_explanations.csv"
df_results = pd.DataFrame(all_results)
df_results.to_csv(output_csv_path, index=False)
print(f"\nAll explanations saved to: {output_csv_path}")
print(f"Batch IDs saved to: {batch_id_file}")
print(f"Error logs saved to: {error_log_file}")
