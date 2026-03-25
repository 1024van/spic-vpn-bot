import hmac
import base64
import json
from hashlib import sha256

from config import CLOUDPAYMENTS_PUBLIC_ID, CLOUDPAYMENTS_API_SECRET


def get_public_id() -> str:
    return CLOUDPAYMENTS_PUBLIC_ID


def verify_signature(raw_body: bytes, header_signature: str) -> bool:
    """
    Проверка подписи CloudPayments в вебхуках:
    X-Content-HMAC = base64( HMAC_SHA256(api_secret, body) )
    """
    if not header_signature or not CLOUDPAYMENTS_API_SECRET:
        return False

    mac = hmac.new(
        CLOUDPAYMENTS_API_SECRET.encode("utf-8"),
        msg=raw_body,
        digestmod=sha256,
    )
    calculated = base64.b64encode(mac.digest()).decode("utf-8")
    return hmac.compare_digest(calculated, header_signature)


def parse_webhook(body: bytes) -> dict:
    return json.loads(body.decode("utf-8"))
