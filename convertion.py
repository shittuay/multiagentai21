import json
import os

# Define the full path to your Firebase Admin SDK key file
# Using os.path.join is safer for cross-OS compatibility, and
# we'll use a raw string (r"...") to avoid backslash issues.
# IMPORTANT: Double-check this path matches where your file truly is!
key_file_path = r"C:\Users\shitt\Downloads\multiagentai21-ae044d4505d2.json"

# --- Added check for file existence ---
if not os.path.exists(key_file_path):
    print(f"Error: Firebase key file not found at '{key_file_path}'")
    exit(1)
# --- End added check ---

try:
    with open(key_file_path, 'r') as f:
        data = json.load(f)

    # Convert the Python dictionary back to a JSON string, minified (no extra whitespace/newlines)
    # This automatically handles proper escaping for shell contexts.
    json_string = json.dumps(data)

    # Print the string. This is the output you will copy.
    print(json_string)

except json.JSONDecodeError as e:
    print(f"Error decoding JSON from file '{key_file_path}': {e}")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)