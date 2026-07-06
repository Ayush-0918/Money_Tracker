import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.ai_service import AIService, AIProvider

@pytest.mark.asyncio
async def test_ai_categorization_success():
    # Mock Provider
    mock_provider = MagicMock(spec=AIProvider)
    mock_provider.get_completion = AsyncMock(return_value='{"category": "Food"}')

    service = AIService(provider=mock_provider)
    category = await service.categorize_transaction("Swiggy", 500.0, "Food delivery")

    assert category == "Food"
    mock_provider.get_completion.assert_called_once()

@pytest.mark.asyncio
async def test_ai_categorization_cache():
    mock_provider = MagicMock(spec=AIProvider)
    mock_provider.get_completion = AsyncMock(return_value='{"category": "Food"}')

    service = AIService(provider=mock_provider)

    # First call
    await service.categorize_transaction("Swiggy", 500.0, "Food delivery")
    # Second call (should hit cache)
    category = await service.categorize_transaction("Swiggy", 200.0, "Lunch")

    assert category == "Food"
    assert mock_provider.get_completion.call_count == 1

@pytest.mark.asyncio
async def test_ai_categorization_fallback():
    mock_provider = MagicMock(spec=AIProvider)
    mock_provider.get_completion = AsyncMock(return_value=None) # Simulate failure

    service = AIService(provider=mock_provider)
    category = await service.categorize_transaction("Unknown", 100.0, "Random")

    assert category is None # Fallback to rules in transaction_service.py
