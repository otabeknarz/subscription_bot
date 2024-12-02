from functools import lru_cache

from .redis_connection import get_redis


class MainBotStates:
    # Start state
    START = "start"

    # Nothing state
    NOTHING = "nothing"

    # Add phone number state
    PHONE_NUMBER = "phone_number"

    # Add bot state
    ENTER_BOT_TOKEN = "enter_bot_token"
    ASSIGN_CHANNEL_TO_BOT = "assign_channel_to_bot"
    COMPLETE_ADD_BOT = "complete_add_bot"

    # Stop bot state
    STOP_BOT = "stop_bot"

    # Add channel state
    ENTER_CHANNEL_ID = "enter_channel_id"
    ENTER_CHANNEL_NAME = "enter_channel_name"
    COMPLETE_ADD_CHANNEL = "complete_add_channel"

    # Add channel to bot state
    ADD_CHANNEL_TO_BOT = "add_channel_to_bot"


class StateManager:
    def __init__(self):
        self.client = get_redis()

    def set_state(
        self, user_id: int, state: str, data: dict = None, update: bool = False
    ):
        """Set the state for a user."""
        if data is None:
            data = {}
        key = f"user:{user_id}:state"
        value = {
            "state": state,
            "data": (
                data
                if not update
                else {**self.get_state_with_data(user_id).get("data"), **data}
            ),
        }
        self.client.set_as_json(key, value)

    def get_state_with_data(self, user_id: int) -> dict | None:
        """Get the state for a user."""
        key = f"user:{user_id}:state"
        state_data = self.client.get_as_json(key)
        return state_data

    def reset_state(self, user_id: int):
        """Reset the state for a user."""
        self.set_state(user_id, MainBotStates.NOTHING)


@lru_cache
def get_state_manager():
    return StateManager()
