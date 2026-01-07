#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import copy
import argparse
import itertools
from collections import Counter
from collections import deque
import logging

import cv2 as cv
import numpy as np
import mediapipe as mp

from utils import CvFpsCalc
from utils.ipc import IPCClient
from model import KeyPointClassifier
from model import PointHistoryClassifier
from logging_config import setup_logging

# Configure logging
logger = setup_logging("gestured.detector", log_file="gestured_detector.log")

class GestureDetector:
    def __init__(self, device=0, width=960, height=540):
        self.cap = cv.VideoCapture(device)
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, height)
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )
        
        self.keypoint_classifier = KeyPointClassifier()
        self.point_history_classifier = PointHistoryClassifier()
        
        self.ipc_client = IPCClient()
        
        self.history_length = 16
        self.point_history = deque(maxlen=self.history_length)
        self.finger_gesture_history = deque(maxlen=self.history_length)

    def run(self):
        logger.info("Starting Gesture Detector...")
        while True:
            # Capture frame
            ret, image = self.cap.read()
            if not ret:
                break
            image = cv.flip(image, 1)  # Mirror
            debug_image = copy.deepcopy(image) # Keep for debug display if needed
            
            # MediaPipe Inference
            image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = self.hands.process(image)
            image.flags.writeable = True

            current_gesture_id = -1
            finger_gesture_id = 0
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Preprocess
                    landmark_list = self._calc_landmark_list(debug_image, hand_landmarks)
                    pre_processed_landmark_list = self._pre_process_landmark(landmark_list)
                    pre_processed_point_history_list = self._pre_process_point_history(debug_image, self.point_history)
                    
                    # Hand Sign Classification
                    current_gesture_id = self.keypoint_classifier(pre_processed_landmark_list)
                    
                    # Point History Update
                    if current_gesture_id == 2:  # Point gesture
                        self.point_history.append(landmark_list[8])
                    else:
                        self.point_history.append([0, 0])
                        
                    # Finger Gesture Classification
                    if len(pre_processed_point_history_list) == (self.history_length * 2):
                        finger_gesture_id = self.point_history_classifier(pre_processed_point_history_list)
                    
                    # Store history for voting (smoothing)
                    self.finger_gesture_history.append(finger_gesture_id)
                    vote_result = Counter(self.finger_gesture_history).most_common()
                    most_common_fg_id = vote_result[0][0]
                    
                    # Emit Event
                    # Determine gesture type
                    gesture_type = "hand_sign"
                    if current_gesture_id == 2: # Point gesture
                        gesture_type = "finger_gesture"
                    
                    from datetime import datetime
                    event = {
                        "gesture_type": gesture_type,
                        "hand_sign_id": current_gesture_id,
                        "finger_gesture_id": most_common_fg_id,
                        "confidence": 1.0,
                        "timestamp": datetime.now().timestamp()
                    }
                    self.ipc_client.send_event(event)

            else:
                self.point_history.append([0, 0])
            
            # Handle ESC
            if cv.waitKey(10) == 27:
                break
                
        self.cap.release()
        cv.destroyAllWindows()

    def _calc_landmark_list(self, image, landmarks):
        image_width, image_height = image.shape[1], image.shape[0]
        landmark_point = []
        for _, landmark in enumerate(landmarks.landmark):
            landmark_x = min(int(landmark.x * image_width), image_width - 1)
            landmark_y = min(int(landmark.y * image_height), image_height - 1)
            landmark_point.append([landmark_x, landmark_y])
        return landmark_point

    def _pre_process_landmark(self, landmark_list):
        temp_landmark_list = copy.deepcopy(landmark_list)
        base_x, base_y = 0, 0
        for index, landmark_point in enumerate(temp_landmark_list):
            if index == 0:
                base_x, base_y = landmark_point[0], landmark_point[1]
            temp_landmark_list[index][0] = temp_landmark_list[index][0] - base_x
            temp_landmark_list[index][1] = temp_landmark_list[index][1] - base_y
        temp_landmark_list = list(itertools.chain.from_iterable(temp_landmark_list))
        max_value = max(list(map(abs, temp_landmark_list)))
        def normalize_(n):
            return n / max_value
        return list(map(normalize_, temp_landmark_list))

    def _pre_process_point_history(self, image, point_history):
        image_width, image_height = image.shape[1], image.shape[0]
        temp_point_history = copy.deepcopy(point_history)
        base_x, base_y = 0, 0
        for index, point in enumerate(temp_point_history):
            if index == 0:
                base_x, base_y = point[0], point[1]
            temp_point_history[index][0] = (temp_point_history[index][0] - base_x) / image_width
            temp_point_history[index][1] = (temp_point_history[index][1] - base_y) / image_height
        return list(itertools.chain.from_iterable(temp_point_history))

if __name__ == '__main__':
    detector = GestureDetector()
    detector.run()
