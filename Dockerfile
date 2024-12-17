# Use a Python base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the Scripts folder into the container
COPY ./Scripts /app/Scripts

# Install the required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port (not necessary for this script but useful for web applications)
EXPOSE 8080


# Install necessary dependencies (if any, add below)
# Example: RUN pip install -r requirements.txt

# Default command to run the Python script
CMD ["python", "/app/Scripts/gpt_explanation_generation.py"]

# # Command to run the Python script
# CMD ["python", "Scripts/gpt_explanation_generation.py"] 
# CMD ["python", "Scripts/GPT/testing_new.py"]  # Command to run your script
