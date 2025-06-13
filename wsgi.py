from flask import Flask, render_template_string
import streamlit.components.v1 as components
import subprocess
import threading
import time

app = Flask(__name__)

# Start Streamlit in background
def start_streamlit():
    subprocess.run(["streamlit", "run", "app.py", "--server.port=8502", "--server.headless=true"])

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Multiagentai21</title>
    </head>
    <body>
        <iframe src="http://localhost:8502" width="100%" height="100%" frameborder="0"></iframe>
    </body>
    </html>
    ''')

if __name__ == "__main__":
    # Start Streamlit in background thread
    streamlit_thread = threading.Thread(target=start_streamlit)
    streamlit_thread.daemon = True
    streamlit_thread.start()
    
    time.sleep(5)  # Wait for Streamlit to start
    app.run(host='0.0.0.0', port=8000)
