import json
from uuid import uuid4

from init import redis_client
from settings import conf


# сохраняет на время. дефолт сутки
def save_redis_temp(key: str, data: dict, storage_time: int = 86400) -> str:
    redis_hash = uuid4().hex[:16]
    redis_client.setex(name=f'{key}-{redis_hash}', time=storage_time, value=json.dumps(data))
    return redis_hash


# сохраняет на время. дефолт сутки
def save_redis_data(key: str, data: dict) -> str:
    redis_hash = uuid4().hex[:16]
    redis_client.set(name=f'{key}-{redis_hash}', value=json.dumps(data))
    return redis_hash


# возвращает данные
def get_redis_data(key: str, del_data: bool = False) -> dict:
    if del_data:
        data = redis_client.getdel(key)
    else:
        data = redis_client.get(key)

    return json.loads(data) if data else {}


# удаляет данные
def del_redis_data(key: str) -> None:
    redis_client.delete(key)
