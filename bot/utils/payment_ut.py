from aiocache import cached, SimpleMemoryCache

import aiohttp
import typing as t

from settings import conf, log_error
# from .redis_ut import get_pay_token_redis, save_pay_token_redis
from enums import UrlTail


# получаем токен
@cached(ttl=86400, cache=SimpleMemoryCache)
async def get_pay_token() -> t.Optional[str]:
    url = conf.pay_url + UrlTail.AUTH.value
    payload = {
        "application_id": conf.application_id,
        "secret": conf.pay_secret,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                data = await response.json()
                if "token" in data:
                    return data["token"]
                else:
                    log_error(f"Ошибка получения токена: {data}", wt=False)
        except aiohttp.ClientError as e:
            log_error(e)


# создаём счёт
# Тестовая карта: 8600 3036 5537 5959 03/26
async def create_invoice(
    invoice_id: str,
    amount: int,
    ofd_items: list[dict],
) -> t.Optional[str]:
    """
    Создаёт инвойс в системе Multicard.
    :param invoice_id: ID инвойса (внутренний ID в твоей системе)
    :param amount: Сумма в тийинах (10000 = 100 сум)
    :param ofd_items: Список позиций для фискализации
    """
    token = await get_pay_token()

    url = conf.pay_url + UrlTail.INVOICE.value
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "store_id": int(conf.store_id),
        "invoice_id": invoice_id,
        "amount": amount * 100,
        "return_url": conf.bot_link,
        "callback_url": conf.callback_url,
        "return_error_url": conf.bot_link,
        "ofd": ofd_items,
    }

    # Удаляем None-поля из payload
    payload = {k: v for k, v in payload.items() if v is not None}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    raise response.text
                data = await response.json()
                if data.get("success"):

                    # for k, v in data.items():
                    #     print(f'{k}: {v}')
                    return data["data"]["checkout_url"]
                else:
                    log_error(f"Ошибка создания счёта:\n{data}", wt=False)
        except aiohttp.ClientError as e:
            log_error(e)

    return None


async def refund_payment(uuid: str) -> dict | None:
    token = await get_pay_token()

    url = f"{conf.pay_url}{UrlTail.PAYMENT.value}/{uuid}"
    headers = {"Authorization": f"Bearer {token}"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.delete(url, headers=headers) as response:
                data = await response.json()
                if data.get("success"):
                    return data["data"]
                else:
                    log_error(f"Ошибка возврата: {data}", wt=False)
        except aiohttp.ClientError as e:
            log_error(e)

    return None
