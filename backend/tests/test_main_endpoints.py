import unittest
from fastapi.testclient import TestClient
from backend.main import app

class TestMainEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        
    def test_message_streaming(self):
        # Test message streaming endpoint with various request parameters
        # Assert expected response status code and content
        pass
        
    def test_system_prompt(self):
        # Test system prompt endpoint
        pass
        
    # Add tests for each modified endpoint
    
    # Add more test methods as needed