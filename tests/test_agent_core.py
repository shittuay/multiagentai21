import pytest
from src.agent_core import AgentType, AgentResponse, MultiAgentCodingAI

def test_agent_type_enum():
    """Test that agent types are properly defined"""
    assert AgentType.AUTOMATION.value == "automation"
    assert AgentType.DATA_ANALYSIS.value == "data_analysis"
    assert AgentType.CUSTOMER_SERVICE.value == "customer_service"
    assert AgentType.CONTENT_CREATION.value == "content_creation"

def test_agent_response():
    """Test AgentResponse creation and attributes"""
    response = AgentResponse(
        content="Test response",
        data={"key": "value"},
        success=True,
        error=None
    )
    assert response.content == "Test response"
    assert response.data == {"key": "value"}
    assert response.success is True
    assert response.error is None

def test_agent_response_error():
    """Test AgentResponse with error"""
    error_msg = "Test error"
    response = AgentResponse(
        content=None,
        data=None,
        success=False,
        error=error_msg
    )
    assert response.content is None
    assert response.data is None
    assert response.success is False
    assert response.error == error_msg

@pytest.fixture
def agent_system():
    """Fixture to create a MultiAgentCodingAI instance"""
    return MultiAgentCodingAI()

def test_agent_system_initialization(agent_system):
    """Test that the agent system initializes properly"""
    assert agent_system is not None
    assert hasattr(agent_system, 'route_request')

def test_invalid_agent_type(agent_system):
    """Test handling of invalid agent type"""
    with pytest.raises(ValueError):
        agent_system.route_request("invalid_type", "test request", {}) 