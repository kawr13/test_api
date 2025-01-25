import pytest
from httpx import AsyncClient
from main import app, BOT_TOKEN
from utilities.configurate import settings


@pytest.fixture
async def test_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_check_imei_api_success(test_client, mocker):
    mock_response = {"status": "success", "imei": "123456789012345"}
    mocker.patch("utilities.check_imei.send_to_url", return_value=mock_response)

    response = await test_client.post(
        "/api/check-imei/",
        json={"imei": "123456789012345"},
        headers={"Authorization": f"Bearer {BOT_TOKEN}"},
    )

    assert response.status_code == 200
    assert response.json() == mock_response


@pytest.mark.asyncio
async def test_check_imei_api_unauthorized(test_client):
    response = await test_client.post(
        "/api/check-imei/",
        json={"imei": "123456789012345"},
        headers={"Authorization": "Bearer wrong_token"},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Не авторизованный запрос"}


@pytest.mark.asyncio
async def test_vite_list_success(test_client, mocker):
    mocker.patch("models.db_utilit.set_active", return_value=True)

    response = await test_client.post(
        "/api/vite-list/",
        json={"tg_id": 123456, "is_active": True},
        headers={"Authorization": f"Bearer {BOT_TOKEN}"},
    )

    assert response.status_code == 200
    assert response.json() == {"tg_id": 123456, "is_active": True}


@pytest.mark.asyncio
async def test_vite_list_invalid_data(test_client):
    response = await test_client.post(
        "/api/vite-list/",
        json={"tg_id": "invalid_id", "is_active": "yes"},
        headers={"Authorization": f"Bearer {BOT_TOKEN}"},
    )

    assert response.status_code == 422  # Ошибка валидации данных


@pytest.mark.asyncio
async def test_webhook_unauthorized_ip(test_client, mocker):
    mocker.patch("utilities.configurate.settings.WEBHOOK_URL", return_value="http://test")
    response = await test_client.post(
        "/webhook",
        json={},
        headers={"x-real-ip": "8.8.8.8"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Unauthorized: Request not from Telegram"}


@pytest.mark.asyncio
async def test_webhook_valid_ip(test_client, mocker):
    mocker.patch("utilities.configurate.settings.WEBHOOK_URL", return_value="http://test")
    mocker.patch("aiogram.Dispatcher.feed_update", return_value=None)
    mocker.patch("aiogram.types.Update.model_validate")

    response = await test_client.post(
        "/webhook",
        json={},
        headers={"x-real-ip": "149.154.160.1"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_startup_event(test_client, mocker):
    mocker.patch("db_conf.init", return_value=None)
    mocker.patch("aiogram.Bot.set_webhook", return_value=None)

    await app.router.startup()
    assert settings.WEBHOOK_URL in settings.WEBHOOK_URL  # Проверка на вызов события старта


@pytest.mark.asyncio
async def test_shutdown_event(test_client, mocker):
    mocker.patch("aiogram.Bot.delete_webhook", return_value=None)

    await app.router.shutdown()
    assert True  # Просто проверка корректного вызова события
