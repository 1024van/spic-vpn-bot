import hashlib
import urllib.parse
from typing import Dict, Optional
from config import FREEKASSA_MERCHANT_ID, FREEKASSA_SECRET1, FREEKASSA_SECRET2

class FreeKassaPayment:
    def __init__(self):
        self.merchant_id = FREEKASSA_MERCHANT_ID
        self.secret1 = FREEKASSA_SECRET1
        self.secret2 = FREEKASSA_SECRET2
        self.base_url = "https://pay.freekassa.ru/"
    
    def generate_signature(self, amount: float, order_id: str) -> str:
        """Генерирует подпись для платежа"""
        # Формат: MD5(merchant_id:amount:secret1:order_id)
        sign_string = f"{self.merchant_id}:{amount}:{self.secret1}:{order_id}"
        return hashlib.md5(sign_string.encode()).hexdigest()
    
    def verify_callback(self, data: Dict) -> bool:
        """Проверяет подпись callback от FreeKassa"""
        # Формат: MD5(merchant_id:amount:secret2:order_id)
        sign_string = f"{self.merchant_id}:{data['AMOUNT']}:{self.secret2}:{data['MERCHANT_ORDER_ID']}"
        expected_sign = hashlib.md5(sign_string.encode()).hexdigest()
        return expected_sign.upper() == data.get('SIGN', '').upper()
    
    def create_payment_url(self, amount: float, order_id: str, description: str = "") -> str:
        """Создаёт URL для оплаты"""
        params = {
            'm': self.merchant_id,
            'oa': amount,
            'o': order_id,
            's': self.generate_signature(amount, order_id),
            'desc': urllib.parse.quote(description),
            'currency': 'RUB'
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.base_url}?{query_string}"

freekassa = FreeKassaPayment()
