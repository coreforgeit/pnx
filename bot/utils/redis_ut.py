import json

from init import redis_client
from settings import conf


# сохраняет на время. дефолт сутки
def save_redis_temp(key: str, data: dict, storage_time: int = 86400) -> None:
    redis_client.setex(name=key, time=storage_time, value=json.dumps(data))


# возвращает данные
def get_redis_data(key: str) -> dict:
    if conf.debug:
        data = redis_client.get(key)
    else:
        data = redis_client.getdel(key)

    return json.loads(data) if data else {}
