import asyncio
import base64
import hmac
import json
from hashlib import sha256

from aiohttp import web

from config import CLOUDPAYMENTS_API_SECRET
from database import db
import logging

logger = logging.getLogger(__name__)

async def handle_pay(request: web.Request) -> web.Response:
    raw_body = await request.read()
    signature = request.headers.get("X-Content-HMAC", "")

    logger.info("CloudPayments webhook raw: %s", raw_body)
    logger.info("CloudPayments webhook signature: %s", signature)

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        logger.error("CloudPayments webhook invalid JSON")
        return web.json_response({"code": 0, "message": "invalid json"}, status=400)

    logger.info("CloudPayments payload parsed: %s", payload)

    model = payload.get("Model") or payload.get("model") or {}
    status = model.get("Status") or model.get("status")
    order_id = (
        model.get("InvoiceId")
        or model.get("invoiceId")
        or model.get("ExternalId")
        or model.get("externalId")
    )

    logger.info("CloudPayments status=%s order_id=%s", status, order_id)

    return web.json_response({"code": 0})

async def handle_pay(request: web.Request) -> web.Response:
    raw_body = await request.read()
    signature = request.headers.get("X-Content-HMAC", "")

    if not _verify_signature(raw_body, signature):
        return web.json_response({"code": 0, "message": "invalid signature"}, status=403)

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        return web.json_response({"code": 0, "message": "invalid json"}, status=400)

    model = payload.get("Model") or payload.get("model") or {}
    status = model.get("Status") or model.get("status")
    order_id = (
        model.get("InvoiceId")
        or model.get("invoiceId")
        or model.get("ExternalId")
        or model.get("externalId")
    )

    if not order_id:
        return web.json_response({"code": 0, "message": "no order_id"}, status=400)

    if status not in ("Completed", "Authorized"):
        return web.json_response({"code": 0, "message": "ignored status"})

    payment = db.get_payment(order_id)
    if not payment:
        return web.json_response({"code": 0, "message": "payment not found"})

    if payment["status"] == "completed":
        return web.json_response({"code": 0, "message": "already completed"})

    db.confirm_payment(order_id)

    from handlers.purchase import deliver_subscription  # чтобы избежать циклического импорта сверху

    asyncio.create_task(
        deliver_subscription(
            request.app["bot"],
            payment["user_id"],
            payment["plan_code"],
            payment_id=order_id,
            amount=payment["amount"],
        )
    )

    return web.json_response({"code": 0})


def _verify_signature(raw_body: bytes, header_signature: str) -> bool:
    if not CLOUDPAYMENTS_API_SECRET or not header_signature:
        return False

    mac = hmac.new(
        CLOUDPAYMENTS_API_SECRET.encode("utf-8"),
        msg=raw_body,
        digestmod=sha256,
    )
    calculated = base64.b64encode(mac.digest()).decode("utf-8")
    return hmac.compare_digest(calculated, header_signature)


async def init_app(bot) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.add_routes([web.post("/api/cloudpayments/pay", handle_pay)])
    return app
