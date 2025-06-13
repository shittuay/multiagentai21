import subprocess
import sys
import os

def handler(event, context):
    """
    Netlify function to run Streamlit app
    """
    
    # Change to the repo directory
    repo_path = "/opt/build/repo"
    os.chdir(repo_path)
    
    # Install requirements if not already installed
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        return {
            'statusCode': 500,
            'body': f'Failed to install requirements: {e.stderr}'
        }
    
    # Run the Streamlit app
    try:
        # For Netlify functions, we need to return the app content
        # This is a simplified approach - you might need to modify based on your specific needs
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html',
            },
            'body': '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Streamlit App</title>
                <meta http-equiv="refresh" content="0; url=/.netlify/functions/streamlit-server">
            </head>
            <body>
                <p>Redirecting to Streamlit app...</p>
            </body>
            </html>
            '''
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error running Streamlit app: {str(e)}'
        }