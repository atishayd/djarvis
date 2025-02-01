import cv2
import logging
from gesture_detection import GestureDetector
from spotify_controller import SpotifyController
# from vlc_controller import VLCController  # Uncomment to use VLC instead
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging at the start of main.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Reduce logging from other libraries
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('spotipy').setLevel(logging.WARNING)

# Create logger for this module
logger = logging.getLogger(__name__)

def main():
    """Main function to run the gesture-controlled music player"""
    try:
        logger.info("Starting AI Virtual DJ...")
        
        # Initialize gesture detector
        logger.info("Initializing gesture detector...")
        gesture_detector = GestureDetector()
        
        # Initialize Spotify controller
        logger.info("Initializing Spotify controller...")
        music_controller = SpotifyController(
            client_id="4fd6ca99c7c345779a3ed425425c5408",
            client_secret="9cdba7f978504a23a60f4dcca3c75ec0"
        )
        
        # Open webcam
        logger.info("Opening webcam...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logger.error("Could not open webcam")
            return

        logger.info("Starting main loop...")
        while True:
            # Read frame from webcam
            ret, frame = cap.read()
            if not ret:
                logger.error("Failed to grab frame")
                break

            # Process frame for gestures
            frame, gesture = gesture_detector.process_frame(frame)
            
            # Handle detected gesture
            if gesture:
                logger.info(f"Detected gesture: {gesture}")
                if gesture in ['swipe_right', 'swipe_left']:
                    music_controller.handle_gesture(gesture)
                else:
                    music_controller.handle_gesture(gesture)

            # Display frame
            cv2.imshow('AI Virtual DJ', frame)

            # Check for quit command
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("Quit command received")
                break

    except Exception as e:
        logger.error("An error occurred in main:", exc_info=True)
        raise
    finally:
        logger.info("Cleaning up...")
        cv2.destroyAllWindows()
        if 'cap' in locals():
            cap.release()

if __name__ == "__main__":
    main() 