from .settings import get_settings

bot_settings = get_settings()


async def account_add(
    chat_id: str, first_name: str, last_name: str, phone: str, username: str, backend
) -> tuple[dict, int] | bool:
    """Add account to backend"""
    response, status_code = await backend.post_data(
        bot_settings.ACCOUNT_ADD_URL,
        data={
            "id": chat_id,
            "name": str(
                first_name + " " + last_name if last_name else first_name
            ).rstrip(),
            "phone_number": phone,
            "username": username,
        },
    )
    if status_code == 201:
        return True
    elif status_code == 400 and response.get("detail") == "Account already exists":
        return False


async def get_my_bots(
    chat_id: str, backend, with_string: bool = False
) -> tuple[list[dict], int] | str | None:
    """Fetch bots from backend"""
    if with_string:
        my_bots, status_code = await backend.fetch_data(
            bot_settings.BOTS_URL + f"?account_id={chat_id}"
        )
        if not any(my_bots):
            return None
        bots = "-----------------------------------\n"
        bots += "\n".join(
            [
                f"🆔: {bot["id"]}\n🔑 {bot.get("token")[:-20] + " * * * * *"}\nUlangan kanal: {bot['channel']['name']}"
                for bot in my_bots
            ]
        )
        return bots
    return await backend.fetch_data(bot_settings.BOTS_URL + f"?account_id={chat_id}")


async def get_my_channels(
    chat_id: str, backend, doesnt_have_bot: bool = False, with_string: bool = False
) -> tuple[list[dict], int] | str | None:
    """Fetch channels from backend"""
    if with_string:
        my_channels, status_code = await backend.fetch_data(
            bot_settings.CHANNELS_URL
            + f"?account_id={chat_id}{'&doesnt_have_bot=1' if doesnt_have_bot else ''}"
        )
        if not any(my_channels):
            return None
        channels = "-----------------------------------\n"
        channels += "\n\n".join(
            [
                f"🆔: {channel.get('id')} | {channel.get('name')}"
                for channel in my_channels
            ]
        )
        return channels

    return await backend.fetch_data(
        bot_settings.CHANNELS_URL
        + f"?account_id={chat_id}{'&doesnt_have_bot=1' if doesnt_have_bot else ''}"
    )
