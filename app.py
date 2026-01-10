
import os
import sys

# Add current directory to path so aadhaar_analytics can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aadhaar_analytics.dashboard.gradio_app import app

if __name__ == "__main__":
    app.launch(server_name="127.0.0.1", server_port=7860)
