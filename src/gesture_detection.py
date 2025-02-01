import cv2
import mediapipe as mp
import numpy as np
import logging
import time

class GestureDetector:
    def __init__(self):
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing GestureDetector...")
        
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        # Add debounce settings
        self.last_gesture_time = 0
        self.play_pause_cooldown = 2.0  # Longer cooldown for play/pause
        self.gesture_cooldown = 0.3  # Reduced from 0.5 to make gestures more responsive
        self.last_gesture = None
        
        # Store initial position for swipe detection
        self.initial_position = None
        # Track movement history
        self.movement_history = []
        # Add swipe thresholds
        self.swipe_threshold = 0.05  # Reduced from 0.1 to make swipes even easier to detect
        self.min_swipe_frames = 3    # Increased from 2 to ensure intentional swipes
        self.movement_history_size = 3  # New parameter to track fewer frames
        self.frame_skip_count = 0  # Add a counter for skipping frames
        self.process_every_n_frames = 4  # e.g. only process every 4th frame
        self.debug_log_interval = 10
        self.debug_log_counter = 0
        self.logger.info("GestureDetector initialized successfully")

    def _is_open_palm(self, hand_landmarks, wrist_index=0):
        """
        Return True if the average distance between each fingertip
        and the wrist is > some threshold, implying fingers extended.
        """
        # Indices for fingertips: thumb_tip=4, index_tip=8, middle_tip=12, ring_tip=16, pinky_tip=20
        fingertip_indices = [4, 8, 12, 16, 20]
        wrist = hand_landmarks.landmark[wrist_index]
        distances = []
        for tip_idx in fingertip_indices:
            tip = hand_landmarks.landmark[tip_idx]
            dx = tip.x - wrist.x
            dy = tip.y - wrist.y
            dist = (dx**2 + dy**2) ** 0.5
            distances.append(dist)
        avg_dist = sum(distances) / len(distances)
        # Adjust 0.12 to taste; bigger means requiring a wider hand spread
        return avg_dist > 0.12

    def _is_closed_fist(self, hand_landmarks, wrist_index=0):
        """
        Return True if all fingertips are close to the wrist, implying a closed fist.
        """
        fingertip_indices = [4, 8, 12, 16, 20]
        wrist = hand_landmarks.landmark[wrist_index]
        distances = []
        for tip_idx in fingertip_indices:
            tip = hand_landmarks.landmark[tip_idx]
            dx = tip.x - wrist.x
            dy = tip.y - wrist.y
            dist = (dx**2 + dy**2) ** 0.5
            distances.append(dist)
        avg_dist = sum(distances) / len(distances)
        # Adjust 0.06 to taste; smaller means requiring a tighter fist
        return avg_dist < 0.06

    def detect_gesture(self, hand_landmarks):
        """
        Identify gestures based on landmark positions.
        """
        try:
            current_time = time.time()
            gesture = None
            
            # Extract palm center and thumb tip for better tracking
            palm_center = hand_landmarks.landmark[0]  # Wrist point
            thumb_tip = hand_landmarks.landmark[4]    # Thumb tip for additional reference
            
            # Use average of palm center and thumb tip for more stable tracking
            current_position = np.array([(palm_center.x + thumb_tip.x)/2, 
                                       (palm_center.y + thumb_tip.y)/2])
            
            # Initialize position tracking if needed
            if self.initial_position is None:
                self.initial_position = current_position
                self.movement_history = []
                return None
            
            # Calculate movement
            movement = current_position - self.initial_position
            self.movement_history.append(movement)
            
            # Keep only recent movements
            if len(self.movement_history) > self.movement_history_size:
                self.movement_history.pop(0)
            
            # Add debug logging for movement tracking
            self.debug_log_counter += 1
            
            # -------------------------------------------------------
            # Refined SWIPE logic using net displacement in the buffer
            # -------------------------------------------------------
            if len(self.movement_history) >= self.min_swipe_frames:
                first_offset = self.movement_history[0]
                last_offset = self.movement_history[-1]
                net_x = last_offset[0] - first_offset[0]
                net_y = last_offset[1] - first_offset[1]
                net_dist = abs(net_x)
                ratio = 0.0
                if abs(net_x) > 1e-3:
                    ratio = abs(net_y / net_x)

                if self.debug_log_counter % self.debug_log_interval == 0:
                    self.logger.debug(f"[SWIPE DEBUG] net_x={net_x:.3f}, net_y={net_y:.3f}, ratio={ratio:.3f}, dist={net_dist:.3f}")
                    self.logger.debug(f"Time since last gesture: {current_time - self.last_gesture_time:.2f}s")

                can_swipe = (
                    len(self.movement_history) >= self.min_swipe_frames
                    and net_dist > 0.08
                    and ratio < 0.5
                    and (current_time - self.last_gesture_time >= self.gesture_cooldown)
                )

                if can_swipe:
                    if net_x > 0:
                        gesture = "swipe_right"
                        self.logger.info("Detected SWIPE RIGHT gesture (net displacement)")
                    else:
                        gesture = "swipe_left"
                        self.logger.info("Detected SWIPE LEFT gesture (net displacement)")

                    self.last_gesture_time = current_time
                    self.initial_position = None
                    self.movement_history = []
                    return gesture

            # --------------------------------------------------------
            # Volume Up / Down logic (vertical net displacement)
            # --------------------------------------------------------
            if not gesture and len(self.movement_history) >= self.min_swipe_frames:
                first_offset = self.movement_history[0]
                last_offset = self.movement_history[-1]
                net_x = last_offset[0] - first_offset[0]
                net_y = last_offset[1] - first_offset[1]

                # We'll say if net_y < -0.08, that's volume_up;
                # if net_y > +0.08, that's volume_down.
                vertical_dist = abs(net_y)
                # Also ensure we haven't used a gesture recently
                if (current_time - self.last_gesture_time >= self.gesture_cooldown):
                    # Check if the movement is primarily vertical
                    # i.e. the vertical motion is significantly bigger than horizontal
                    if abs(net_y) > abs(net_x) * 1.5 and vertical_dist > 0.08:
                        if net_y < 0:
                            gesture = "volume_up"
                            self.logger.info("Detected VOLUME UP gesture (vertical displacement)")
                        else:
                            gesture = "volume_down"
                            self.logger.info("Detected VOLUME DOWN gesture (vertical displacement)")

                        self.last_gesture_time = current_time
                        self.initial_position = None
                        self.movement_history = []
                        return gesture

            # Only check for play/pause if no swipe was detected
            if not gesture:
                if current_time - self.last_gesture_time >= self.play_pause_cooldown:
                    if self._is_open_palm(hand_landmarks):
                        gesture = "play"
                        self.logger.info("Detected PLAY gesture - (Open palm / fingers extended)")
                    elif self._is_closed_fist(hand_landmarks):
                        gesture = "pause"
                        self.logger.info("Detected PAUSE gesture - (Closed fist)")
            
            # Update tracking
            if gesture:
                self.initial_position = None
                self.movement_history = []
                self.last_gesture_time = current_time
            else:
                self.initial_position = current_position

            return gesture

        except Exception as e:
            self.logger.exception("Error in detect_gesture:")
            return None

    def process_frame(self, frame):
        """
        Process a single frame and return detected gestures
        """
        try:
            # (Optional) Downscale frame before Mediapipe to reduce CPU load
            # e.g. down to 320x180
            frame = cv2.resize(frame, (320, 180), interpolation=cv2.INTER_AREA)
            
            # Skip frames to reduce CPU usage
            self.frame_skip_count += 1
            if self.frame_skip_count % self.process_every_n_frames != 0:
                # Return frame without processing any gestures
                return frame, None
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(frame_rgb)
            
            # Check for BOTH HANDS RAISED => "quit"
            if results.multi_hand_landmarks and len(results.multi_hand_landmarks) >= 2:
                # For simplicity, check the first two hands' wrists
                wrist1 = results.multi_hand_landmarks[0].landmark[0]
                wrist2 = results.multi_hand_landmarks[1].landmark[0]
                # If both wrists are above y=0.3, consider that "quit"
                if wrist1.y < 0.3 and wrist2.y < 0.3:
                    gesture = "quit"
                    self.logger.info("Detected TWO HANDS RAISED - Quitting")
                    return frame, gesture
            
            gesture = None
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame, 
                        hand_landmarks, 
                        self.mp_hands.HAND_CONNECTIONS
                    )
                    gesture = self.detect_gesture(hand_landmarks)
                    if gesture:  # Only process the first valid gesture
                        break
            else:
                # Reset position tracking when no hand is detected
                self.initial_position = None
                self.movement_history = []
            
            return frame, gesture
        except Exception as e:
            self.logger.exception("Error in process_frame:")
            return frame, None 