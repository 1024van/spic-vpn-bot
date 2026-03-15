import hashlib
import urllib.parse
from typing import Dict

from config import FREEKASSA_MERCHANT_ID, FREEKASSA_SECRET1, FREEKASSA_SECRET2


class FreeKassaPayment:
    def __init__(self):
        self.merchant_id = FREEKASSA_MERCHANT_ID
        self.secret1 = FREEKASSA_SECRET1
        self.secret2 = FREEKASSA_SECRET2
        # Домен, как в рабочем примере FreeKassa
        self.base_url = "https://pay.freekassa.net/"

    def generate_signature(self, amount: int, order_id: str, currency: str = "RUB") -> str:
        """Формат: MD5(merchant_id:amount:secret1:currency:order_id)"""
        sign_string = f"{self.merchant_id}:{amount}:{self.secret1}:{currency}:{order_id}"
        return hashlib.md5(sign_string.encode("utf-8")).hexdigest()

    def verify_callback(self, data: Dict) -> bool:
        """
        Проверяет подпись callback от FreeKassa.

        Формат: MD5(MERCHANT_ID:AMOUNT:secret2:MERCHANT_ORDER_ID)
        """
        sign_string = (
            f"{data['MERCHANT_ID']}:"
            f"{data['AMOUNT']}:"
            f"{self.secret2}:"
            f"{data['MERCHANT_ORDER_ID']}"
        )
        expected_sign = hashlib.md5(sign_string.encode("utf-8")).hexdigest()
        return expected_sign.upper() == data.get("SIGN", "").upper()

    def create_payment_url(self, amount: float, order_id: str) -> str:
        """Создаёт URL для оплаты в формате FreeKassa."""
        amount_int = int(amount)
        currency = "RUB"

        signature = self.generate_signature(amount_int, order_id, currency)

        params = {
            "m": str(self.merchant_id),
            "oa": str(amount_int),
            "o": order_id,
            "s": signature,
            "currency": currency,
            "us_order_id": order_id,
        }

        query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote_plus)
        return f"{self.base_url}?{query_string}"


freekassa = FreeKassaPayment()
