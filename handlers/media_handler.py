#!/usr/bin/env python3
"""macOS media control handler without requiring Accessibility permissions."""

import logging
import platform
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class MediaHandler:
    """Handle media playback control with platform-specific implementations."""
    
    def __init__(self):
        self.system = platform.system()
    
    def play_pause(self) -> bool:
        """Toggle play/pause."""
        try:
            if self.system == "Darwin":
                # Use AppleScript WITHOUT accessibility requirement
                # This uses the Media Center instead of System Events
                script = '''
                tell application "Music"
                    playpause
                end tell
                '''
                subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
                return True
            elif self.system == "Linux":
                subprocess.run(['playerctl', 'play-pause'], check=True)
                return True
            elif self.system == "Windows":
                import pyautogui
                pyautogui.press('playpause')
                return True
        except Exception as e:
            logger.error(f"Failed to play/pause: {e}")
            return False
    
    def next_track(self) -> bool:
        """Skip to next track."""
        try:
            if self.system == "Darwin":
                script = '''
                tell application "Music"
                    next track
                end tell
                '''
                subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
                return True
            elif self.system == "Linux":
                subprocess.run(['playerctl', 'next'], check=True)
                return True
        except Exception as e:
            logger.error(f"Failed to skip track: {e}")
            return False
    
    def previous_track(self) -> bool:
        """Go to previous track."""
        try:
            if self.system == "Darwin":
                script = '''
                tell application "Music"
                    previous track
                end tell
                '''
                subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
                return True
            elif self.system == "Linux":
                subprocess.run(['playerctl', 'previous'], check=True)
                return True
        except Exception as e:
            logger.error(f"Failed to go to previous track: {e}")
            return False


class VolumeHandler:
    """Handle system volume control."""
    
    def __init__(self):
        self.system = platform.system()
    
    def get_volume(self) -> Optional[int]:
        """Get current system volume (0-100)."""
        try:
            if self.system == "Darwin":
                output = subprocess.check_output(
                    ['osascript', '-e', 'output volume of (get volume settings)'],
                    text=True
                ).strip()
                return int(output)
            elif self.system == "Linux":
                output = subprocess.check_output(
                    ['amixer', 'get', 'Master'],
                    text=True
                )
                # Parse percentage from amixer output
                import re
                match = re.search(r'\[(\d+)%\]', output)
                if match:
                    return int(match.group(1))
        except Exception as e:
            logger.error(f"Failed to get volume: {e}")
        return None
    
    def set_volume(self, level: int) -> bool:
        """Set system volume (0-100)."""
        try:
            level = max(0, min(100, level))  # Clamp 0-100
            
            if self.system == "Darwin":
                script = f'set volume output volume {level}'
                subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
                return True
            elif self.system == "Linux":
                subprocess.run(['amixer', 'set', 'Master', f'{level}%'], check=True)
                return True
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False
    
    def volume_up(self, delta: int = 5) -> bool:
        """Increase volume by delta."""
        current = self.get_volume()
        if current is not None:
            return self.set_volume(current + delta)
        return False
    
    def volume_down(self, delta: int = 5) -> bool:
        """Decrease volume by delta."""
        current = self.get_volume()
        if current is not None:
            return self.set_volume(current - delta)
        return False


class ScreenshotHandler:
    """Handle screenshot capture."""
    
    def __init__(self):
        self.system = platform.system()
    
    def take_screenshot(self, save_to: str = None) -> bool:
        """Take screenshot and optionally save to file."""
        try:
            if self.system == "Darwin":
                # macOS: interactive screenshot (Cmd+Shift+5)
                subprocess.run(['screencapture', '-i'], check=False)
                return True
            elif self.system == "Linux":
                subprocess.run(['gnome-screenshot'], check=False)
                return True
            elif self.system == "Windows":
                import pyautogui
                img = pyautogui.screenshot()
                if save_to:
                    img.save(save_to)
                return True
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return False
