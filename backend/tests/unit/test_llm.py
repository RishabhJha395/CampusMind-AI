import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
from app.services.llm.openrouter import OpenRouterService

@pytest.fixture
def openrouter_service():
    return OpenRouterService(api_key="test-key", primary_model="test-primary", fallback_model="test-fallback")

def test_build_system_prompt(openrouter_service):
    context = ["Fact 1: DTU is in Delhi.", "Fact 2: DTU has great placements."]
    prompt = openrouter_service.build_system_prompt(context, "DTU")
    
    assert "You are the official AI assistant for DTU." in prompt
    assert "Fact 1: DTU is in Delhi." in prompt
    assert "Fact 2: DTU has great placements." in prompt
    assert "--- Context 1 ---" in prompt

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_generate_response_success(mock_post, openrouter_service):
    # Mock successful response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "DTU is in Delhi."}}
        ]
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response
    
    response = await openrouter_service.generate_response("Where is DTU?", ["DTU is in Delhi."], "DTU")
    
    assert response == "DTU is in Delhi."
    mock_post.assert_called_once()
    
    # Check payload
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["model"] == "test-primary"
    assert kwargs["json"]["stream"] is False

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_fallback_on_rate_limit(mock_post, openrouter_service):
    # First call fails with 429
    error_response = httpx.Response(429, request=httpx.Request("POST", "url"), text="Rate limit")
    error = httpx.HTTPStatusError("429 Error", request=error_response.request, response=error_response)
    
    # Second call succeeds
    success_response = MagicMock()
    success_response.json.return_value = {
        "choices": [
            {"message": {"content": "Fallback response."}}
        ]
    }
    success_response.raise_for_status = MagicMock()
    
    mock_post.side_effect = [error, success_response]
    
    response = await openrouter_service.generate_response("Test query", [], "TestUni")
    
    assert response == "Fallback response."
    assert mock_post.call_count == 2
    
    # Check models used
    call_1_kwargs = mock_post.call_args_list[0][1]
    call_2_kwargs = mock_post.call_args_list[1][1]
    
    assert call_1_kwargs["json"]["model"] == "test-primary"
    assert call_2_kwargs["json"]["model"] == "test-fallback"

@pytest.mark.asyncio
@patch("httpx.AsyncClient.send")
@patch("httpx.AsyncClient.build_request")
async def test_generate_response_stream(mock_build_request, mock_send, openrouter_service):
    # Mock building request
    mock_req = MagicMock()
    mock_build_request.return_value = mock_req
    
    # Mock streaming response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    
    async def mock_aiter_lines():
        yield "data: {\"choices\": [{\"delta\": {\"content\": \"Hello \"}}]}"
        yield "data: {\"choices\": [{\"delta\": {\"content\": \"World!\"}}]}"
        yield "data: [DONE]"
        
    mock_response.aiter_lines = mock_aiter_lines
    mock_send.return_value = mock_response
    
    chunks = []
    async for chunk in openrouter_service.generate_response_stream("Test query", [], "TestUni"):
        chunks.append(chunk)
        
    assert chunks == ["Hello ", "World!"]
    mock_send.assert_called_once_with(mock_req, stream=True)
