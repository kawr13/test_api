import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from models.model import User


@pytest.mark.asyncio
async def test_add_user_handler():
    # Mock dependencies
    state = AsyncMock(spec=FSMContext)
    call = AsyncMock(spec=CallbackQuery)
    call.data = "add_user"

    # Create mock users
    mock_users = [
        User(tg_id=1, is_active=True),
        User(tg_id=2, is_active=False)
    ]

    # Patch User.filter to return mock users
    with patch('models.model.User.filter', return_value=AsyncMock()) as mock_filter, \
            patch('models.model.User.filter().all', return_value=mock_users), \
            patch('utilities.sender.send_message') as mock_send_message:
        mock_filter.return_value.all.return_value = mock_users

        from paste_2 import add_user_handler
        await add_user_handler(call, state)

        # Assert state was updated with users
        state.update_data.assert_called_with({'user': mock_users})

        # Assert message was sent
        mock_send_message.assert_called_once()

        # Check the message content
        message_text = mock_send_message.call_args[0][1]
        assert "Список пользователей" in message_text
        assert "1. 1." in message_text
        assert "2. 2." in message_text


@pytest.mark.asyncio
async def test_block_handler():
    # Mock dependencies
    state = AsyncMock(spec=FSMContext)
    call = AsyncMock(spec=CallbackQuery)
    call.data = "is_block+123"

    # Create a mock user
    mock_user = User(tg_id=123, is_active=True)

    # Patch dependencies
    with patch('models.model.User.filter') as mock_filter, \
            patch('models.model.User.filter().first', return_value=mock_user), \
            patch('utilities.bot_conf.bot.send_message', return_value=AsyncMock()), \
            patch('paste_2.add_user_handler') as mock_add_user_handler:
        # Set up the mock filter to return the mock user
        mock_filter.return_value.first.return_value = mock_user

        from paste_2 import block_handler
        await block_handler(call, state)

        # Assert the user's active status was toggled
        assert mock_user.is_active == False

        # Assert user was saved
        assert hasattr(mock_user, 'save')

        # Assert add_user_handler was called
        mock_add_user_handler.assert_called_once()


def test_imei_validation():
    from paste_2 import is_valid_imei

    # Test valid IMEI
    valid_imei = "490014205973859"
    message_mock = AsyncMock(spec=Message)
    message_mock.text = valid_imei
    state_mock = AsyncMock(spec=FSMContext)

    # We'll need to modify the test to handle the coroutine
    async def run_test():
        result = await is_valid_imei(message_mock, state_mock)
        assert result == True

    import asyncio
    asyncio.run(run_test())

    # Test invalid IMEI formats
    invalid_imeis = [
        "12345",  # Too short
        "123456789012345678",  # Too long
        "abcdefghijklmnop",  # Non-numeric
        "490014205973850"  # Invalid check digit
    ]

    for imei in invalid_imeis:
        message_mock.text = imei

        async def run_invalid_test():
            result = await is_valid_imei(message_mock, state_mock)
            assert result == False

        asyncio.run(run_invalid_test())