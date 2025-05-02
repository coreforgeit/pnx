import aiohttp
import typing as t

from settings import conf, log_error
from .redis_ut import get_pay_token_redis, save_pay_token_redis
from enums import UrlTail


# получаем токен
async def get_pay_token() -> t.Optional[str]:
    url = conf.pay_url + UrlTail.AUTH.value
    payload = {
        "application_id": conf.application_id,
        "secret": conf.pay_secret,
    }
    log_error(url, wt=False)
    log_error(payload, wt=False)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                log_error(response.text, wt=False)
                response.raise_for_status()
                data = await response.json()

                log_error(f'get_pay_token', wt=False)
                log_error(data, wt=False)

                if "token" in data:
                    return data["token"]
                else:
                    print("Ошибка получения токена:", data)
        except aiohttp.ClientError as e:
            log_error(e)


# создаём счёт
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
    token = get_pay_token_redis()
    log_error(f'token:{token}', wt=False)
    if not token:
        token = await get_pay_token()
        log_error(f'token2:{token}', wt=False)
        save_pay_token_redis(token)

    url = conf.pay_url + UrlTail.INVOICE.value
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "store_id": conf.store_id,
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
                response.raise_for_status()
                data = await response.json()
                if data.get("success"):

                    # for k, v in data.items():
                    #     print(f'{k}: {v}')

                    # return data["data"]["short_link"]
                    return data["data"]["checkout_url"]
                else:
                    print("Ошибка создания счёта:", data)
        except aiohttp.ClientError as e:
            print("Ошибка запроса:", e)

    return None


async def refund_payment(uuid: str) -> dict | None:
    token = get_pay_token_redis()
    log_error(f'token:{token}', wt=False)
    if not token:
        token = await get_pay_token()
        log_error(f'token2:{token}', wt=False)
        save_pay_token_redis(token)

    url = f"{conf.pay_url}{UrlTail.INVOICE.value}/{uuid}"
    headers = {"Authorization": f"Bearer {token}"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.delete(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                if data.get("success"):
                    return data["data"]
                else:
                    print("Ошибка возврата:", data)
        except aiohttp.ClientError as e:
            print("Ошибка запроса:", e)

    return None
