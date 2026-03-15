from aiogram import Router, F
from aiogram.types import Message
from database import db
from keyboards import admin_menu, main_menu
from config import ADMIN_IDS
from utils.trusttunnel import trusttunnel
import sqlite3
import os

router = Router()

@router.message(F.text == "🔐 Админ-панель")
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    await message.answer(
        "🔐 <b>Панель администратора</b>",
        reply_markup=admin_menu()
    )

@router.message(F.text == "📊 Статистика")
async def admin_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    DB_PATH = os.getenv("DATABASE_PATH", "/opt/vpn_bot/vpn_bot.db")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM subscriptions WHERE is_active = 1")
    active_subs = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(amount) FROM payments WHERE status = 'completed'")
    revenue = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'")
    pending_payments = cursor.fetchone()[0]
    
    conn.close()
    
    await message.answer(
        f"📊 <b>Статистика:</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"✅ Активных подписок: {active_subs}\n"
        f"⏳ Ожидают оплаты: {pending_payments}\n"
        f"💰 Общий доход: {revenue}₽"
    )

@router.message(F.text == "🔄 Перезапустить Endpoint")
async def restart_endpoint(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        trusttunnel._restart_endpoint()
        await message.reply("✅ Endpoint перезапущен")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {str(e)}")

@router.message(F.text == "⬅️ Назад")
async def back_to_main(message: Message):
    await message.answer(
        "Главное меню",
        reply_markup=main_menu(message.from_user.id in ADMIN_IDS)
    )