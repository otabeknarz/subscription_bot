from functools import lru_cache
from redis import Redis
import json


class RedisConnection(Redis):
    def __init__(self):
        super().__init__(host="localhost", port=6379, db=0)

    def set_active_bots(self, bots: list):
        self.set_as_json("active_bots", bots)

    def get_active_bots(self) -> list[dict]:
        return self.get_as_json("active_bots")

    def set_as_json(self, key: str, value: dict | list, expire: int = None):
        self.set(key, json.dumps(value), ex=expire)

    def get_as_json(self, key: str) -> dict | list:
        data: bytes = self.get(key)
        return json.loads(data.decode("utf-8")) if data else None


@lru_cache
def get_redis():
    return RedisConnection()
