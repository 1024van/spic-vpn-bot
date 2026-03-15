#!/usr/bin/env python3
"""
Webhook server для приёма callback от FreeKassa
Запускать отдельно или через systemd
"""

import asyncio
from aiohttp import web
from aiogram import Bot
from config import BOT_TOKEN, ADMIN_IDS
from database import db
from handlers.purchase import deliver_subscription
from utils.payments import freekassa

async def freekassa_callback(request):
    """Обработчик callback от FreeKassa"""
    data = await request.post()
    data_dict = dict(data)
    
    # Проверяем подпись
    if not freekassa.verify_callback(data_dict):
        return web.Response(text="Bad sign", status=400)
    
    # Получаем данные платежа
    order_id = data_dict.get('MERCHANT_ORDER_ID')
    amount = data_dict.get('AMOUNT')
    
    # Проверяем статус
    payment = db.get_payment(order_id)
    if not payment:
        return web.Response(text="Order not found", status=404)
    
    if payment['status'] == 'completed':
        return web.Response(text="Already processed")
    
    # Подтверждаем платеж
    db.confirm_payment(order_id)
    
    # Выдаём подписку через бот
    bot = Bot(token=BOT_TOKEN)
    await deliver_subscription(bot, payment['user_id'], payment['plan_code'])
    await bot.session.close()
    
    # Отвечаем FreeKassa
    return web.Response(text="OK")

async def init_app():
    app = web.Application()
    app.router.add_post('/webhook/freekassa', freekassa_callback)
    return app

if __name__ == '__main__':
    app = init_app()
    web.run_app(app, host='localhost', port=8080)