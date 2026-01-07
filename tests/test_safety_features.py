#!/usr/bin/env python3
"""Comprehensive tests for safety features."""

import unittest
import time
from safety.rate_limiter import TokenBucket, GestureDebouncer, SafetyManager


class TestRateLimiter(unittest.TestCase):
    """Test token bucket rate limiting."""
    
    def setUp(self):
        self.bucket = TokenBucket(capacity=5, refill_rate=1.0)
    
    def test_initial_tokens(self):
        """Should start with full capacity."""
        self.assertEqual(self.bucket.tokens, 5)
    
    def test_token_consumption(self):
        """Should consume tokens on successful request."""
        self.assertTrue(self.bucket.is_allowed())
        # Tokens might be slightly refilled due to execution time, so we check range
        self.assertLessEqual(self.bucket.tokens, 4.1) 
        self.assertGreaterEqual(self.bucket.tokens, 3.9)
    
    def test_burst_limit(self):
        """Should deny requests when out of tokens."""
        # Consume all tokens
        for _ in range(5):
            self.assertTrue(self.bucket.is_allowed())
        
        # Next request should fail
        self.assertFalse(self.bucket.is_allowed())
    
    def test_token_refill(self):
        """Should refill tokens over time."""
        # Consume all tokens
        for _ in range(5):
            self.bucket.is_allowed()
        
        # Wait for refill
        time.sleep(1.1)  # Wait slightly more than 1 second
        
        # Should have tokens again
        self.assertTrue(self.bucket.is_allowed())


class TestGestureDebouncer(unittest.TestCase):
    """Test gesture debouncing."""
    
    def setUp(self):
        self.debouncer = GestureDebouncer(debounce_ms=100)
    
    def test_first_gesture_allowed(self):
        """First gesture should always be allowed."""
        self.assertTrue(self.debouncer.should_process(1))
    
    def test_rapid_gesture_blocked(self):
        """Rapid gestures should be blocked."""
        self.assertTrue(self.debouncer.should_process(1))
        self.assertFalse(self.debouncer.should_process(1))  # Too soon
    
    def test_different_gestures_independent(self):
         """Different gestures should be debounced independently."""
         self.assertTrue(self.debouncer.should_process(1))
         self.assertTrue(self.debouncer.should_process(2))


class TestSafetyManager(unittest.TestCase):
    def setUp(self):
        self.manager = SafetyManager()
        
    def test_kill_switch(self):
        self.assertTrue(self.manager.is_safe_to_execute("g1", "a1"))
        self.manager.toggle_kill_switch()
        self.assertFalse(self.manager.is_safe_to_execute("g1", "a1"))

if __name__ == '__main__':
    unittest.main()
