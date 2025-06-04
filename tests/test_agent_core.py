import unittest
from src.agent_core import AgentType, Agent, process_request


class TestAgentType(unittest.TestCase):
    """Test cases for AgentType enum."""

    def test_agent_type_values(self):
        """Test that agent types have correct values."""
        self.assertEqual(AgentType.AUTOMATION.value, "automation")
        self.assertEqual(AgentType.DATA_ANALYSIS.value, "data_analysis")
        self.assertEqual(AgentType.CUSTOMER_SERVICE.value, "customer_service")
        self.assertEqual(AgentType.CONTENT_CREATION.value, "content_creation")


class TestAgent(unittest.TestCase):
    """Test cases for Agent class."""

    def test_agent_initialization(self):
        """Test agent initialization with different types."""
        agent = Agent(AgentType.AUTOMATION)
        self.assertEqual(agent.agent_type, AgentType.AUTOMATION)
        self.assertIsNotNone(agent.model)

    def test_agent_response(self):
        """Test agent response generation."""
        agent = Agent(AgentType.AUTOMATION)
        response = agent.process_request("test request")
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)

    def test_invalid_agent_type(self):
        """Test handling of invalid agent type."""
        with self.assertRaises(ValueError):
            Agent("invalid_type")


class TestProcessRequest(unittest.TestCase):
    """Test cases for process_request function."""

    def test_process_request_with_valid_type(self):
        """Test process_request with valid agent type."""
        response = process_request("test request", AgentType.AUTOMATION)
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)

    def test_process_request_with_invalid_type(self):
        """Test process_request with invalid agent type."""
        with self.assertRaises(ValueError):
            process_request("test request", "invalid_type")


if __name__ == "__main__":
    unittest.main()
