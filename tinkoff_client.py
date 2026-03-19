import requests
import hashlib
from config import TINKOFF_TERMINAL_KEY, TINKOFF_PASSWORD, TINKOFF_SUCCESS_URL, TINKOFF_FAIL_URL


TINKOFF_API_URL = "https://rest-api-test.tinkoff.ru/eacq/v2"  # тестовый URL, см. доку


def _generate_token(params: dict) -> str:
    """
    У T‑банка токен обычно считается как SHA256 от отсортированных полей + пароль.
    Конкретную схему проверь в их доке для твоего API (интернет-эквайринг).
    Здесь примерный вариант, подправим после просмотра доки в ЛК.
    """
    # Берём все ключи кроме Token, сортируем
    filtered = {k: v for k, v in params.items() if k != "Token" and v is not None}
    sorted_items = sorted(filtered.items(), key=lambda x: x[0])

    # Склеиваем значения в строку
    data = "".join(str(v) for _, v in sorted_items)
    data += TINKOFF_PASSWORD

    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def create_payment(amount_rub: int, order_id: str, description: str, customer_email: str | None = None):
    """
    Создаёт платёж через Init и возвращает (payment_id, payment_url).
    amount_rub — сумма в рублях.
    """
    amount_kopecks = amount_rub * 100

    payload = {
        "TerminalKey": TINKOFF_TERMINAL_KEY,
        "Amount": amount_kopecks,
        "OrderId": order_id,
        "Description": description,
        "SuccessURL": TINKOFF_SUCCESS_URL,
        "FailURL": TINKOFF_FAIL_URL,
    }

    if customer_email:
        payload["CustomerKey"] = customer_email

    # Генерируем токен
    payload["Token"] = _generate_token(payload)

    resp = requests.post(f"{TINKOFF_API_URL}/Init", json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("Success"):
        raise RuntimeError(f"Tinkoff Init error: {data}")

    payment_id = data.get("PaymentId") or data.get("PaymentId".lower())
    payment_url = data.get("PaymentURL") or data.get("PaymentURL".lower())

    if not payment_url:
        raise RuntimeError(f"No PaymentURL in response: {data}")

    return payment_id, payment_url