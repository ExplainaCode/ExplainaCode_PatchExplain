# Use a Python base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the local files to the container's working directory
COPY . /app

# Install the required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port (not necessary for this script but useful for web applications)
EXPOSE 8080

# Command to run the Python script
CMD ["python", "Scripts/GPT/gpt_explanation_generation.py"] 
