import openai
import pandas as pd
import os
import re

# Load environment variables
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")

# Set OpenAI API Key
openai.api_key = OPEN_AI_API_KEY

# Directories
input_dir = '..../Data/1000_record_chunks/'  # Input folder with chunk files
output_dir = '..../Data/100k_dataset/gpt/'  # Output folder to save explanations
os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists

sample_size = 1  # Sample size for each chunk


def get_gpt_explanation(buggy_code, fixed_code):
    """
    Function to get a concise explanation using OpenAI's GPT model.
    """
    # Use double curly braces {{ }} to escape literal curly braces in f-strings
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

    ---

    ### Your Task:

    **Buggy Code:**
    {buggy_code}

    **Fixed Code:**
    {fixed_code}

    **Why the fixed code is correct:**"""
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that explains bug fixes clearly."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        temperature=0.7
    )
    return response['choices'][0]['message']['content'].strip()

def natural_sort_key(file_name):
    """
    Extract numeric parts of file names for natural sorting.
    Example: '1000_chunk_10.csv' -> [10]
    """
    return [int(text) if text.isdigit() else text for text in re.split(r'(\d+)', file_name)]


# Process all chunk files
files = [file for file in os.listdir(input_dir) if file.endswith('.csv')]
files.sort(key=natural_sort_key)[:5]  # Sort files in natural order

for file in files:
    input_path = os.path.join(input_dir, file)
    output_file_name = file.replace(".csv", "_only_gpt_4-0_mini.csv")
    output_path = os.path.join(output_dir, output_file_name)

    print(f"Processing {file}...")
    
    # Load the data and sample rows
    df = pd.read_csv(input_path)
    df = df.sample(min(sample_size, len(df)))  # Take a sample of the data
    
    # Apply explanation generation
    df['gpt_explanation'] = df.apply(lambda row: get_gpt_explanation(row['buggy_code'], row['fixed_code']), axis=1)
    
    # Save the output
    df.to_csv(output_path, index=False)
    print(f"Explanations saved to {output_path}")

print("Processing complete for all chunk files!")
