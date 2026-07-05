import os
import sys
from dotenv import load_dotenv

# Ensure the app module can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.youtube_service import YouTubeService

# Load environment variables (needs GROQ_API_KEY)
load_dotenv()

def test_youtube_transcription():
    print("=== Testing YouTube Transcription Engine ===")
    
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not found in environment variables. Please add it to your .env file.")
        return

    # Use a short YouTube video for testing (e.g., a 1-minute YouTube Shorts or short clip)
    # This URL is an example (Me at the zoo - the first YouTube video ever, 19 seconds)
    test_url = "https://youtu.be/eHS0WIWNtu0?si=r0hvcMZwPfmyifK_"
    
    print(f"Target URL: {test_url}")
    print("Initiating download and transcription (this may take a few seconds)...")
    
    try:
        transcript = YouTubeService.get_transcript(test_url)
        print("\n--- Transcription Result ---")
        print(transcript)
        print("\n----------------------------")
        
        if transcript and not transcript.startswith("Error"):
            print("SUCCESS: YouTube transcription engine works!")
        else:
            print("FAILED: Did not get a valid transcript back.")
            
    except Exception as e:
        print(f"FAILED: Exception occurred during testing: {e}")

if __name__ == "__main__":
    test_youtube_transcription()
