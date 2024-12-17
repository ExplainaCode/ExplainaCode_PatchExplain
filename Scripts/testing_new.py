import os

# Print the current working directory
print("Current Working Directory:", os.getcwd())

# Print the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
print("Script Directory:", script_dir)

# Define the input directory
input_dir = os.path.join(script_dir, '../Data/1000_record_chunks/')
input_dir = os.path.normpath(input_dir)
print("Expected Input Directory:", input_dir)

# Verify if the input directory exists
if not os.path.exists(input_dir):
    print(f"Directory does not exist: {input_dir}")
    raise FileNotFoundError(f"Directory {input_dir} does not exist.")

# List files in the directory
files = [file for file in os.listdir(input_dir) if file.endswith('.csv')]
print("Files in the input directory:", files)
