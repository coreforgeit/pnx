import json
from uuid import uuid4

from init import redis_client
from settings import conf
from enums import Key


# сохраняет на время. дефолт сутки
def save_redis_temp(key: str, data: dict, storage_time: int = 86400) -> str:
    redis_hash = uuid4().hex[:16]
    redis_client.setex(name=f'{key}-{redis_hash}', time=storage_time, value=json.dumps(data))
    return redis_hash


# сохраняет на время. дефолт сутки
def save_redis_data(key: str, data: dict, with_hash: bool = True) -> str:
    redis_hash = uuid4().hex[:16]
    redis_client.set(name=f'{key}-{redis_hash}', value=json.dumps(data))
    return redis_hash


# сохраняет на время. дефолт сутки
def save_pay_token_redis(token: str) -> None:
    redis_client.setex(name=Key.PAY_TOKEN.value, value=token, time=86400)
    # redis_client.setex(name=f'{key}-{redis_hash}', time=86400, value=json.dumps(data))


# возвращает данные
def get_pay_token_redis() -> str | None:
    raw_token = redis_client.get(Key.PAY_TOKEN.value)
    return raw_token.decode("utf-8") if raw_token else None


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
