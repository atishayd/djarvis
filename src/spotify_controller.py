import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging
import time

# Configure logging for spotify_controller
logger = logging.getLogger(__name__)

class SpotifyController:
    def __init__(self, client_id, client_secret):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Spotify controller...")
        
        # Update scopes to include all required permissions
        scope = " ".join([
            "user-modify-playback-state",  # Control playback
            "user-read-playback-state",    # Get playback state
            "user-read-currently-playing", # Get current track
            "app-remote-control",          # Remote control
            "streaming",                   # Control playback
            "user-read-private"           # Get subscription details
        ])
        
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://localhost:8888/callback",
            scope=scope,
            open_browser=True
        ))
        
        # Verify authentication
        try:
            user = self.sp.current_user()
            # Get user's subscription type more reliably
            user_info = self.sp.me()
            account_type = user_info.get('product', 'unknown')
            
            if account_type != 'premium':
                self.logger.warning(f"Non-premium account detected. Some features may not work. Account type: {account_type}")
            
            self.logger.info(f"Successfully authenticated Spotify account for user: {user.get('display_name', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Failed to authenticate: {str(e)}")
            raise

        self.is_playing = False
        self._current_volume = 50
        self.last_gesture = None
        self.gesture_repeat_cooldown = 1.0  # 1 second local cooldown
        self.last_gesture_time = 0.0

    def handle_gesture(self, gesture):
        """Handle the detected gesture."""
        try:
            current_time = time.time()
            # Skip if same gesture repeated too quickly
            if gesture == self.last_gesture and (current_time - self.last_gesture_time < self.gesture_repeat_cooldown):
                self.logger.debug(f"Ignoring repeated gesture: {gesture}")
                return
            
            self.logger.debug(f"Processing gesture: {gesture}")
            self.last_gesture = gesture
            self.last_gesture_time = current_time

            if gesture == "play":
                self.play()
            elif gesture == "pause":
                self.pause()
            elif gesture == "swipe_right":
                self.logger.info("Detected swipe right, skipping to next track")
                self.next_track()
            elif gesture == "swipe_left":
                self.logger.info("Detected swipe left, going to previous track")
                self.previous_track()
        except Exception as e:
            self.logger.error(f"Error handling gesture: {str(e)}")

    def _ensure_active_device(self):
        """Check for active device and provide user feedback if none found."""
        devices = self.sp.devices()
        logger.debug(f"Available devices: {devices}")
        
        if not devices['devices']:
            logger.warning("No Spotify devices found! Please open Spotify on any device")
            return False
            
        # Check for any active device
        active_devices = [d for d in devices['devices'] if d['is_active']]
        if not active_devices:
            logger.warning("No active Spotify device found! Please start playing something on Spotify")
            return False
            
        return True

    def handle_action(self, action):
        try:
            if not self._ensure_active_device():
                return

            if action == "play_pause":
                self._toggle_playback()
            elif action == "next":
                self.sp.next_track()
            elif action == "previous":
                self.sp.previous_track()
            elif action == "volume_up":
                self._adjust_volume(10)
            elif action == "volume_down":
                self._adjust_volume(-10)
            elif action == "mute":
                self._toggle_mute()
        except Exception as e:
            logger.error(f"Error handling action {action}: {str(e)}")

    def _toggle_playback(self):
        try:
            playback = self.sp.current_playback()
            if playback and playback['is_playing']:
                logger.info("Pausing playback")
                self.sp.pause_playback()
            else:
                logger.info("Starting playback")
                self.sp.start_playback()
        except Exception as e:
            logger.error(f"Error toggling playback: {str(e)}")

    def _adjust_volume(self, change):
        try:
            self._current_volume = max(0, min(100, self._current_volume + change))
            logger.info(f"Setting volume to {self._current_volume}")
            self.sp.volume(self._current_volume)
        except Exception as e:
            logger.error(f"Error adjusting volume: {str(e)}")

    def _toggle_mute(self):
        try:
            if self._current_volume > 0:
                logger.info("Muting")
                self.sp.volume(0)
            else:
                logger.info("Unmuting")
                self.sp.volume(50)
                self._current_volume = 50
        except Exception as e:
            logger.error(f"Error toggling mute: {str(e)}")

    def play(self):
        """Start playback on active device."""
        try:
            devices = self.sp.devices()
            self.logger.info(f"Found devices: {devices}")
            
            if not devices['devices']:
                self.logger.warning("No Spotify devices found! Please open Spotify on any device")
                return
            
            active_device = None
            for device in devices['devices']:
                self.logger.info(f"Device: {device['name']}, ID: {device['id']}, Active: {device['is_active']}")
                if device['is_active']:
                    active_device = device
                    break
            
            if not active_device:
                # Try to activate the first available device
                active_device = devices['devices'][0]
                try:
                    self.sp.transfer_playback(device_id=active_device['id'], force_play=True)
                    time.sleep(1)  # Give Spotify time to transfer
                except Exception as e:
                    self.logger.error(f"Failed to activate device: {str(e)}")
                    return

            self.logger.info(f"Starting playback on device: {active_device['name']}")
            
            # Get current playback state
            current = self.sp.current_playback()
            self.logger.debug(f"Current playback state: {current}")
            
            try:
                if not current or not current.get('is_playing'):
                    # Try to resume from last position
                    self.sp.start_playback(device_id=active_device['id'])
                else:
                    # If already playing, just ensure we're on the right device
                    self.sp.transfer_playback(device_id=active_device['id'], force_play=True)
                self.is_playing = True
            except spotipy.exceptions.SpotifyException as e:
                self.logger.error(f"Spotify Error: {str(e)}")
                if e.http_status == 403:
                    self.logger.error("Please make sure Spotify is open and a song is loaded")
                    # Try to play the last played track or a default playlist
                    try:
                        recent = self.sp.current_user_recently_played(limit=1)
                        if recent and recent['items']:
                            track_uri = recent['items'][0]['track']['uri']
                            self.logger.info(f"Attempting to play last played track: {track_uri}")
                            self.sp.start_playback(device_id=active_device['id'], uris=[track_uri])
                        else:
                            self.logger.info("No recent tracks, playing default playlist")
                            self.sp.start_playback(device_id=active_device['id'], 
                                                 context_uri="spotify:playlist:37i9dQZF1DXcBWIGoYBM5M")
                    except Exception as e2:
                        self.logger.error(f"Failed to start playback: {str(e2)}")
                raise
        except Exception as e:
            self.logger.error(f"Error in play(): {str(e)}")

    def pause(self):
        """Pause playback on active device."""
        try:
            devices = self.sp.devices()
            active_device = next((d for d in devices['devices'] if d['is_active']), None)
            if active_device:
                self.logger.info("Pausing playback")
                self.sp.pause_playback(device_id=active_device['id'])
                self.is_playing = False
            else:
                self.logger.warning("No active device found")
        except Exception as e:
            self.logger.error(f"Error in pause(): {str(e)}")

    def next_track(self):
        """Skip to next track."""
        try:
            devices = self.sp.devices()
            active_device = next((d for d in devices['devices'] if d['is_active']), None)
            if active_device:
                self.logger.info(f"Next track on device: {active_device['name']}")
                self.sp.next_track(device_id=active_device['id'])
            else:
                self.logger.warning("No active device found")
        except Exception as e:
            self.logger.error(f"Error in next_track(): {str(e)}")

    def previous_track(self):
        """Go back to previous track."""
        try:
            devices = self.sp.devices()
            active_device = next((d for d in devices['devices'] if d['is_active']), None)
            if active_device:
                self.logger.info(f"Previous track on device: {active_device['name']}")
                self.sp.previous_track(device_id=active_device['id'])
            else:
                self.logger.warning("No active device found")
        except Exception as e:
            self.logger.error(f"Error in previous_track(): {str(e)}") 