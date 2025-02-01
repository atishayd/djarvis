import vlc
import time

class VLCController:
    def __init__(self):
        self.player = vlc.MediaPlayer()
        self._current_volume = 50
        self._is_playing = False
        self.last_gesture = None
        self.last_gesture_time = 0.0
        self.throttle_seconds = 1.0  # Only process gestures if 1s has passed

    def load_media(self, path):
        self.player.set_media(vlc.Media(path))

    def handle_action(self, action):
        if action == "play_pause":
            self._toggle_playback()
        elif action == "next":
            # Implement playlist navigation
            pass
        elif action == "previous":
            # Implement playlist navigation
            pass
        elif action == "volume_up":
            self._adjust_volume(10)
        elif action == "volume_down":
            self._adjust_volume(-10)
        elif action == "mute":
            self._toggle_mute()

    def _toggle_playback(self):
        if self._is_playing:
            self.player.pause()
        else:
            self.player.play()
        self._is_playing = not self._is_playing

    def _adjust_volume(self, change):
        self._current_volume = max(0, min(100, self._current_volume + change))
        self.player.audio_set_volume(self._current_volume)

    def _toggle_mute(self):
        if self._current_volume > 0:
            self.player.audio_set_volume(0)
        else:
            self.player.audio_set_volume(50)
            self._current_volume = 50

    def handle_gesture(self, gesture):
        now = time.time()
        if gesture == self.last_gesture and (now - self.last_gesture_time < self.throttle_seconds):
            return
        self.last_gesture = gesture
        self.last_gesture_time = now

        # ... 
        # do something for play/pause/seek, etc.
        # ... 