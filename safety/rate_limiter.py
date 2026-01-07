#!/usr/bin/env python3
"""Rate limiting and debouncing for gesture actions."""

import time
import threading
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_tokens: int = 10  # Max actions per refill period
    refill_rate: float = 1.0  # Tokens per second
    burst_size: int = 5  # Allow up to 5 consecutive actions


class TokenBucket:
    """Token bucket rate limiter."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def is_allowed(self, cost: int = 1) -> bool:
        """Check if action is allowed (and consume tokens)."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            
            # Refill tokens
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate
            )
            self.last_refill = now
            
            # Check if we have enough tokens
            if self.tokens >= cost:
                self.tokens -= cost
                return True
            return False


class GestureDebouncer:
    """Debounce rapid gesture triggers."""
    
    def __init__(self, debounce_ms: int = 200):
        """
        Args:
            debounce_ms: Minimum time between gestures (milliseconds)
        """
        self.debounce_ms = debounce_ms
        self.last_gesture_time: Dict[int, float] = defaultdict(float)
        self.lock = threading.Lock()
    
    def should_process(self, gesture_id: int) -> bool:
        """Check if gesture should be processed (respects debounce)."""
        with self.lock:
            now = time.time() * 1000  # Convert to milliseconds
            last_time = self.last_gesture_time[gesture_id]
            
            if now - last_time >= self.debounce_ms:
                self.last_gesture_time[gesture_id] = now
                return True
            return False


class SafetyManager:
    """Unified safety feature manager."""
    
    def __init__(self):
        self.rate_limiters: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(capacity=10, refill_rate=1.0)
        )
        self.debouncers: Dict[str, GestureDebouncer] = defaultdict(
            lambda: GestureDebouncer(debounce_ms=200)
        )
        self.kill_switch_enabled = True
        self.locked = False
    
    def check_rate_limit(self, action_id: str, cost: int = 1) -> bool:
        """Check if action is rate-limited."""
        return self.rate_limiters[action_id].is_allowed(cost)
    
    def check_debounce(self, gesture_id: str) -> bool:
        """Check if gesture should be debounced."""
        return self.debouncers[gesture_id].should_process(gesture_id)
    
    def is_safe_to_execute(self, gesture_id: str, action_id: str) -> bool:
        """Check all safety constraints."""
        if not self.kill_switch_enabled:
            return False
        
        if self.locked:
            return False
        
        if not self.check_debounce(gesture_id):
            return False
        
        if not self.check_rate_limit(action_id):
            return False
        
        return True
    
    def toggle_kill_switch(self):
        """Emergency stop for gesture control."""
        self.kill_switch_enabled = not self.kill_switch_enabled
    
    def lock(self):
        """Lock all gesture actions (e.g., during password entry)."""
        self.locked = True
    
    def unlock(self):
        """Unlock gesture actions."""
        self.locked = False
