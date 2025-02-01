# AI Virtual DJ

Control your music with hand gestures using computer vision!

## Features
- Real-time hand gesture recognition
- Support for both Spotify and local music playback
- Intuitive gesture controls for common music actions

## Installation

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   
   # On Windows:
   .\venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Getting Spotify Credentials

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account (must be a Premium account)
3. Click "Create an App"
4. Fill in the app name (e.g., "AI Virtual DJ") and description
5. Once created, you'll see your Client ID on the dashboard
6. Click "Show Client Secret" to reveal your Client Secret
7. Click "Edit Settings"
8. Add `http://localhost:8888/callback` to the "Redirect URIs" section
9. Save the settings

## Configuration

1. Open `src/main.py`
2. Replace the placeholder credentials with your Spotify credentials:
   ```python
   music_controller = SpotifyController(
       client_id="YOUR_CLIENT_ID",      # Replace with your Client ID
       client_secret="YOUR_CLIENT_SECRET"  # Replace with your Client Secret
   )
   ```

## Running the Application

1. Make sure your virtual environment is activated
2. Run the application:
   ```bash
   python src/main.py
   ```
3. On first run, a browser window will open asking you to log in to Spotify
4. After authentication, the application will start

## Gesture Controls
- Open Palm: Play/Pause
- Swipe Right: Next Track
- Swipe Left: Previous Track
- Move Up: Increase Volume
- Move Down: Decrease Volume
- Fist: Mute/Unmute

## Requirements
- Python 3.7+
- Webcam
- Spotify Premium account (for Spotify control)
- Internet connection for Spotify authentication

## Troubleshooting

### Common Issues:
1. **ModuleNotFoundError**: Make sure you've activated your virtual environment and installed requirements
2. **Spotify Authentication Error**: 
   - Verify your credentials are correct
   - Ensure the redirect URI matches exactly
   - Check that you have a Premium account
3. **Webcam Not Found**: 
   - Ensure your webcam is connected
   - Try changing `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)` if you have multiple cameras

### Need Help?
If you encounter issues:
1. Check that all requirements are installed: `pip freeze`
2. Verify your Spotify credentials are correct
3. Ensure your webcam is working in other applications 