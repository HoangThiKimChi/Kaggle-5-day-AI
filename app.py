import sys
import os

# Add scripts/ directory to Python path so that all imports inside app.py can resolve correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

# Import the actual streamlit app from scripts/app.py and run it
import app

if __name__ == "__main__":
    app.main()
