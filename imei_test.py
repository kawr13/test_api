import os
import pytest
import aiohttp
import json
from unittest.mock import patch, AsyncMock
from utilities.check_imei import send_to_url


@pytest.mark.asyncio
async def test_send_to_url_success():
    # Sample IMEI for testing
    test_imei = "356735111052198"

    # Mock response data
    mock_response_data = {
        "properties": {
            "deviceName": "Test Device",
            "meid": "Test MEID",
            "imei2": "Test IMEI2",
            "serial": "Test Serial"
        }
    }

    # Mock the aiohttp ClientSession and post method
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_response_data
        mock_post.return_value.__aenter__.return_value = mock_response

        async with aiohttp.ClientSession() as session:
            result = await send_to_url(test_imei)

            # Assert the correct URL was called
            mock_post.assert_called_once_with(
                "https://api.imeicheck.net/v1/checks",
                headers={
                    'Authorization': f'Bearer {os.getenv("IMEI_TOKEN_SANDBOX")}',
                    'Accept-Language': 'en',
                    'Content-Type': 'application/json'
                },
                data=json.dumps({
                    "deviceId": test_imei,
                    "serviceId": 12
                })
            )

            # Assert the response matches expected data
            assert result == mock_response_data


@pytest.mark.asyncio
async def test_send_to_url_network_error():
    # Sample IMEI for testing
    test_imei = "356735111052198"

    # Mock the aiohttp ClientSession to raise a network error
    with patch('aiohttp.ClientSession.post', side_effect=aiohttp.ClientError("Network error")):
        with pytest.raises(aiohttp.ClientError):
            await send_to_url(test_imei)


def test_required_environment_variables():
    # Test that required environment variables are set
    assert os.getenv("IMEI_TOKEN_SANDBOX"), "IMEI_TOKEN_SANDBOX environment variable is not set"
    assert os.getenv("IMEI_TOKEN_PRODUCTION"), "IMEI_TOKEN_PRODUCTION environment variable is not set"