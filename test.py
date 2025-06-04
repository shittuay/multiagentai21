import os

from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS"
)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/c/Users/shitt/multiagentai21-key.json"
import streamlit as st

st.write("Hello World")
try:
    from google.cloud import bigquery

    client = bigquery.Client()
    print("✅ BigQuery authentication successful!")
    print(f"Project ID: {client.project}")
except Exception as e:
    print(f"❌ BigQuery error: {e}")

try:
    import google.generativeai as genai

    # You'll need to set your Gemini API key
    print("✅ Gemini AI library imported successfully!")
except Exception as e:
    print(f"❌ Gemini AI error: {e}")
