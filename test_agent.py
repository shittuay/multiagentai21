# File: tests/test_agent.py
import unittest
from src.agent_core import HackathonAgent

class TestHackathonAgent(unittest.TestCase):
    def setUp(self):
        self.agent = HackathonAgent()
    
    def test_content_generation(self):
        result = self.agent.generate_content("Write a brief summary about AI")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 10)
    
    def test_full_pipeline(self):
        result = self.agent.process_request("Create a business summary")
        self.assertIn('generated_content', result)
        self.assertEqual(result['status'], 'success')

if __name__ == '__main__':
    unittest.main()