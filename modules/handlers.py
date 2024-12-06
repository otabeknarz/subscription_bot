from telethon.tl.custom import Message

from .functions import get_my_channels, get_my_bots, account_add
from .keyboards import MainBotKeyboards, MainBotInlineKeyboards
from .settings import get_settings, Settings
from .state_manager import get_state_manager, MainBotStates, StateManager
from .task_manager import get_task_manager, TaskManager
from .rate_limiter import get_rate_limiter_from_memory, RateLimiter

bot_settings: Settings = get_settings()
state: StateManager = get_state_manager()
task_manager: TaskManager = get_task_manager()
rate_limiter: RateLimiter = get_rate_limiter_from_memory(bot_settings.MAIN_BOT_ID, bot_settings.MAIN_BOT_USERNAME)


async def start_handler(event: Message, backend, *args, **kwargs):
    # Set the state to start
    state.set_state(event.chat.id, MainBotStates.START)

    # Add account event start
    response = await account_add(
        event.chat.id,
        event.sender.first_name,
        event.sender.last_name,
        event.sender.phone,
        event.sender.username,
        backend,
    )
    if response:
        await rate_limiter.respond(
            event=event,
            message="Assalomu alaykum, Xush kelibsiz!",
            buttons=MainBotKeyboards.main_keyboard,
        )
    else:
        await rate_limiter.respond(
            event=event,
            message="Siz allaqachon ro'yxatdan o'tgansiz!",
            buttons=MainBotKeyboards.main_keyboard,
        )

    state.set_state(event.chat.id, MainBotStates.NOTHING)


async def fetch_bots_handler(event, backend, *args, **kwargs):
    bots = await get_my_bots(event.chat.id, backend, with_string=True)
    await rate_limiter.respond(
        event=event,
        message=f"Mening botlarim:\n{bots}" if bots else "Sizda botlar yo'q",
        buttons=MainBotKeyboards.main_keyboard,
    )


async def fetch_channels_handler(event, backend, *args, **kwargs):
    my_channels = await get_my_channels(event.chat.id, backend, with_string=True)
    await rate_limiter.respond(
        event=event,
        message=(
            f"Mening kanallarim:\n{my_channels}"
            if my_channels
            else "Sizda kanallar yo'q"
        ),
        buttons=MainBotKeyboards.main_keyboard,
    )


# Add channel handlers
async def enter_channel_id(event, *args, **kwargs):
    state.set_state(event.chat.id, MainBotStates.ENTER_CHANNEL_ID)
    await rate_limiter.respond(
        event=event,
        message="Kanal ID sini kiriting:",
        buttons=MainBotKeyboards.cancel_keyboard,
    )


async def enter_channel_name(event, backend, *args, **kwargs):
    state.set_state(
        event.chat.id,
        MainBotStates.ENTER_CHANNEL_NAME,
        data={"channel_id": event.message.message},
        update=True,
    )
    await rate_limiter.respond(
        event=event,
        message="Endi kanal nomini kiriting:",
        buttons=MainBotKeyboards.cancel_keyboard,
    )


async def complete_add_channel(event, backend, *args, **kwargs):
    state.set_state(
        event.chat.id,
        MainBotStates.ADD_CHANNEL_TO_BOT,
        data={"channel_name": event.message.message},
        update=True,
    )
    state_data = state.get_state_with_data(event.chat.id)
    response, status_code = await backend.post_data(
        bot_settings.CHANNEL_ADD_URL,
        data={
            "id": state_data.get("data").get("channel_id"),
            "name": state_data.get("data").get("channel_name"),
            "owner": event.chat.id,
        },
    )
    if status_code == 201:
        await rate_limiter.respond(
            event=event,
            message="Kanal muvaffaqiyatli qo'shildi!",
            buttons=MainBotKeyboards.main_keyboard,
        )
    else:
        await rate_limiter.respond(
            event=event,
            message="Kanal qo'shishda xatolik yuz berdi!",
            buttons=MainBotKeyboards.main_keyboard,
        )
    state.reset_state(event.chat.id)


# Add bot handlers
async def enter_bot_token(event, *args, **kwargs):
    state.set_state(event.chat.id, MainBotStates.ENTER_BOT_TOKEN)
    await rate_limiter.respond(
        event=event,
        message="Bot tokenini kiriting:",
        buttons=MainBotKeyboards.cancel_keyboard,
    )


async def assign_channel_to_bot(event, backend, *args, **kwargs):
    result, status_code = await backend.fetch_data(
        bot_settings.TELEGRAM_GET_ME + f"{event.message.message}/getMe"
    )
    if status_code != 200:
        await rate_limiter.respond(
            event=event,
            message="Bot topilmadi!",
            buttons=MainBotKeyboards.main_keyboard,
        )
        state.reset_state(event.chat.id)
        return
    bot_data = result.get("result")
    state.set_state(
        event.chat.id,
        MainBotStates.ASSIGN_CHANNEL_TO_BOT,
        data={
            "bot_token": event.message.message,
            "bot_id": bot_data.get("id"),
            "bot_name": bot_data.get("first_name"),
            "bot_username": bot_data.get("username"),
        },
        update=True,
    )

    inline_keyboard = await MainBotInlineKeyboards.available_channels(
        event.chat.id, bot_data.get("id"), backend
    )
    if not inline_keyboard:
        await rate_limiter.respond(
            event=event,
            message="Sizda kanallar yo'q! avval kanal qo'shing",
            buttons=MainBotKeyboards.main_keyboard,
        )
        state.reset_state(event.chat.id)
        return
    await rate_limiter.respond(
        event=event, message="Botga ulash uchun kanal tanlang:", buttons=inline_keyboard
    )


async def complete_add_bot(event, backend, *args, **kwargs):
    state_data = state.get_state_with_data(event.chat.id)
    response, status_code = await backend.post_data(
        bot_settings.BOT_ADD_URL,
        data={
            "id": state_data.get("data").get("bot_id"),
            "name": state_data.get("data").get("bot_name"),
            "token": state_data.get("data").get("bot_token"),
            "username": state_data.get("data").get("bot_username"),
            "channel_id": state_data.get("data").get("channel_id"),
            "owner": event.chat.id,
        },
    )
    if status_code == 201:
        from .models import get_main_bot, MainBot, TelegramBot

        main_bot: MainBot = get_main_bot()
        bot: TelegramBot = TelegramBot(
            bot_id=response.get("id"),
            bot_token=response.get("token"),
            bot_username=response.get("username"),
            bot_owner=response.get("owner"),
            is_running=response.get("is_running"),
        )
        main_bot.bots.append(bot)
        task_manager.add_task(response.get("id"), TaskManager.BOTS, bot.start())

        await rate_limiter.respond(
            event=event,
            message="Bot muvaffaqiyatli qo'shildi!",
            buttons=MainBotKeyboards.main_keyboard,
        )
    else:
        await rate_limiter.respond(
            event=event,
            message="Bot qo'shishda xatolik yuz berdi!",
            buttons=MainBotKeyboards.main_keyboard,
        )
    state.reset_state(event.chat.id)


# Stop bot handlers
async def change_bot_status_handler(event, backend, *args, **kwargs):
    state.set_state(event.chat.id, MainBotStates.STOP_BOT)
    my_bots, status_code = await get_my_bots(event.chat.id, backend)

    if not any(my_bots):
        await rate_limiter.respond(
            event=event,
            message="Sizda ishga tushirilgan botlar yo'q!",
            buttons=MainBotKeyboards.main_keyboard,
        )
        state.reset_state(event.chat.id)
        return

    change_bot_status_keyboard = (
        await MainBotInlineKeyboards.change_bot_status_keyboard(my_bots)
    )
    await rate_limiter.respond(
        event=event,
        message="To'xtatilayotgan botni tanlang:",
        buttons=change_bot_status_keyboard,
    )


async def send_40_messages(event, *args, **kwargs):
    for i in range(40):
        await rate_limiter.respond(event=event, message=f"Message {i}")
    return True


async def cancel_handler(event, *args, **kwargs):
    state_data = state.get_state_with_data(event.chat.id)
    if state_data.get("state") == MainBotStates.NOTHING:
        await rate_limiter.respond(
            event=event,
            message="Bekor qilishga hech nima yo'q!",
            buttons=MainBotKeyboards.main_keyboard,
        )
        return
    state.reset_state(event.chat.id)
    await rate_limiter.respond(
        event=event,
        message="Amal bekor qilindi!",
        buttons=MainBotKeyboards.main_keyboard,
    )
    return


async def handle_callback(event, backend, *args, **kwargs):
    data = event.data.decode().split(":")
    state_data = state.get_state_with_data(event.chat.id)

    if (
        data[0] == "assign"
        and state_data.get("state") == MainBotStates.ASSIGN_CHANNEL_TO_BOT
    ):
        state.set_state(
            event.chat.id,
            MainBotStates.COMPLETE_ADD_BOT,
            data={"bot_id": data[1], "channel_id": data[2]},
            update=True,
        )
        await rate_limiter.respond(
            event=event, message="Botga ulash uchun kanal tanlandi!"
        )
        await complete_add_bot(event, backend)

    elif (
        data[0] == "change_bot_status"
        and state_data.get("state") == MainBotStates.STOP_BOT
    ):
        response, status_code = await backend.patch_data(
            bot_settings.BOT_UPDATE_URL + f"{data[1]}/",
            data={"is_running": bool(int(data[2]))},
        )
        if status_code == 200:
            await rate_limiter.respond(
                event=event,
                message=(
                    f"Bot @{response.get('username')} to'xtatildi!"
                    if data[2] == "0"
                    else f"Bot @{response.get('username')} ishga tushirildi!"
                ),
                buttons=MainBotKeyboards.main_keyboard,
            )
            from .models import get_main_bot, MainBot

            main_bot: MainBot = get_main_bot()
            if data[2] == "0":
                main_bot.bots.remove(main_bot.get_bot_object(data[1]))
                task_manager.remove_task(data[1], TaskManager.BOTS)
            else:
                task_manager.add_task(
                    data[1], TaskManager.BOTS, main_bot.get_bot_object(data[1]).start()
                )

        state.reset_state(event.chat.id)

    else:
        await rate_limiter.delete(event=event)
        state.reset_state(event.chat.id)


async def do_nothing(*args, **kwargs):
    return True
