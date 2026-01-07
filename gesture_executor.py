#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import json
import time
import subprocess
import threading
import logging
import os
import yaml
from collections import defaultdict
from datetime import datetime

from handlers.media_handler import MediaHandler, VolumeHandler, ScreenshotHandler
from safety.rate_limiter import SafetyManager
from logging_config import setup_logging

# Setup logging
logger = setup_logging("gestured.executor", log_file="gestured_executor.log")


class ActionDispatcher:
    """Maps gesture events to OS actions with safety validation."""
    
    def __init__(self, config_path='config/gesture_config.yaml'):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        abs_config_path = os.path.join(script_dir, config_path)
        
        with open(abs_config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.media_handler = MediaHandler()
        self.volume_handler = VolumeHandler()
        self.screenshot_handler = ScreenshotHandler()
        self.safety_manager = SafetyManager()
        
        # Override safety defaults from config
        safety_conf = self.config.get('safety', {})
        if not safety_conf.get('enable_kill_switch', True):
            self.safety_manager.toggle_kill_switch()

        logger.info(f"ActionDispatcher initialized with {len(self.config['gestures'])} gestures")
    
    def dispatch(self, gesture_event: dict) -> bool:
        """
        Process gesture event and execute corresponding OS action.
        """
        try:
            gesture_type = gesture_event.get('gesture_type')
            hand_sign_id = gesture_event.get('hand_sign_id')
            finger_gesture_id = gesture_event.get('finger_gesture_id')
            confidence = gesture_event.get('confidence', 0.0)
            
            # Identify the gesture being triggered
            active_gesture_id = None
            active_config = None
            
            # Map event to config
            for name, config in self.config['gestures'].items():
                if gesture_type == 'hand_sign' and name.startswith('hand_') and config['id'] == hand_sign_id:
                     active_gesture_id = name
                     active_config = config
                     break
                if gesture_type == 'finger_gesture' and name.startswith('finger_') and config['id'] == finger_gesture_id:
                     active_gesture_id = name
                     active_config = config
                     break

            if not active_config:
                return False
            
            # Use SafetyManager
            # Rate limiting is per-action type usually, or per gesture. We'll check per-gesture for debounce, per-action for rate limit.
            # Actually, let's simplify and use gesture_id for everything, as the SafetyManager API is flexible.
            if not self.safety_manager.is_safe_to_execute(active_gesture_id, active_gesture_id):
                 # logger.debug(f"Safety Check Failed for {active_gesture_id}")
                 return False

            # Check Confidence
            if confidence < 0.6:
                return False
            
            # EXECUTE ACTIONS
            actions = active_config.get('actions', [])
            success_any = False
            for action in actions:
                action_type = action.get('type')
                
                if self._execute_action(action_type, action):
                    success_any = True
                    # Calculate Latency
                    detection_ts = gesture_event.get('timestamp')
                    latency_ms = "N/A"
                    if detection_ts:
                        latency_ms = (datetime.now().timestamp() - detection_ts) * 1000
                        latency_ms = f"{latency_ms:.2f}ms"
                    
                    logger.info(f"✓ Executed: {action_type} for {active_gesture_id} [Latency: {latency_ms}]")
                else:
                    logger.warning(f"✗ Failed: {action_type} for {active_gesture_id}")
            
            return success_any
        
        except Exception as e:
            logger.error(f"Error dispatching gesture: {e}", exc_info=True)
            return False
    
    def _execute_action(self, action_type: str, action_config: dict) -> bool:
        """Execute OS action using Handlers. Returns True if successful."""
        try:
            if action_type == "noop":
                return True
            
            elif action_type == "media_play":
                return self.media_handler.play_pause()
            
            elif action_type == "media_pause":
                return self.media_handler.play_pause()
            
            elif action_type == "volume_up":
                delta = action_config.get('value', 5)
                return self.volume_handler.volume_up(delta)
            
            elif action_type == "volume_down":
                delta = action_config.get('value', 5)
                return self.volume_handler.volume_down(delta)
            
            elif action_type == "screenshot":
                return self.screenshot_handler.take_screenshot()
            
            else:
                logger.warning(f"Unknown action type: {action_type}")
                return False
        
        except Exception as e:
            logger.error(f"Error in action execution: {e}")
            return False


class GestureExecutor:
    """Main executor service."""
    
    def __init__(self, socket_path='/tmp/gestured.sock', config_path='config/gesture_config.yaml'):
        self.socket_path = socket_path
        self.dispatcher = ActionDispatcher(config_path)
        self.running = True
    
    def run(self):
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
            
        server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_socket.bind(self.socket_path)
        server_socket.listen(1)
        
        logger.info(f"GestureExecutor listening on {self.socket_path}")
        
        try:
            while self.running:
                try:
                    connection, _ = server_socket.accept()
                    t = threading.Thread(target=self._handle_client, args=(connection,))
                    t.daemon = True
                    t.start()
                except KeyboardInterrupt:
                    self.running = False
                    break
        finally:
            server_socket.close()
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)
    
    def _handle_client(self, connection):
        try:
            while True:
                import struct
                header = connection.recv(4)
                if not header: break
                msg_len = struct.unpack('>I', header)[0]
                data = connection.recv(msg_len)
                if not data: break
                
                event = json.loads(data.decode('utf-8'))
                self.dispatcher.dispatch(event)
        except Exception as e:
            logger.error(f"Client error: {e}")
        finally:
            connection.close()


if __name__ == '__main__':
    executor = GestureExecutor()
    executor.run()
