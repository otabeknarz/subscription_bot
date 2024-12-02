from telethon.tl.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRow,
    ReplyInlineMarkup,
    KeyboardButtonCallback,
)

from .functions import get_my_channels
from .settings import get_settings, Settings

bot_settings: Settings = get_settings()


class MainBotKeyboards:
    main_keyboard = ReplyKeyboardMarkup(
        rows=[
            KeyboardButtonRow(
                [
                    KeyboardButton("Mening botlarim"),
                    KeyboardButton("Mening kanallarim"),
                ]
            ),
            KeyboardButtonRow(
                [
                    KeyboardButton("Bot larimni boshqarish"),
                ]
            ),
            KeyboardButtonRow(
                [
                    KeyboardButton("Kanal qo'shish"),
                    KeyboardButton("Bot qo'shish"),
                ]
            ),
        ],
        resize=True,
    )

    cancel_keyboard = ReplyKeyboardMarkup(
        rows=[KeyboardButtonRow([KeyboardButton("Bekor qilish")])],
        resize=True,
    )


class MainBotInlineKeyboards:
    @staticmethod
    async def change_bot_status_keyboard(bots: list[dict]) -> ReplyInlineMarkup:
        return ReplyInlineMarkup(
            rows=[
                KeyboardButtonRow(
                    [
                        KeyboardButtonCallback(
                            text=f"{bot.get('name')} | {bot.get('username')}"
                            f"{' | 🟢' if bot.get('is_running') else ' | 🔴'}",
                            data=f"change_bot_status:{bot.get('id')}:{int(not bot.get('is_running'))}".encode(),
                        )
                    ]
                )
                for bot in bots
            ]
        )

    @staticmethod
    async def available_channels(
        account_id, bot_id, backend
    ) -> ReplyInlineMarkup | None:
        my_channels, status_code = await get_my_channels(
            account_id, backend, doesnt_have_bot=True
        )
        if not any(my_channels):
            return None

        return ReplyInlineMarkup(
            rows=[
                KeyboardButtonRow(
                    [
                        KeyboardButtonCallback(
                            text=f"{channel['name']}",
                            data=f"assign:{bot_id}:{channel['id']}".encode(),
                        )
                    ]
                )
                for channel in my_channels
            ]
        )
