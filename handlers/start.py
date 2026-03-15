from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import db
from keyboards import main_menu
from config import ADMIN_IDS

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    
    # Добавляем пользователя в БД
    db.add_user(user_id, username)
    
    is_admin = user_id in ADMIN_IDS
    
    welcome_text = """
👋 Добро пожаловать в <b>TrustTunnel VPN</b>!

🔒 <b>Преимущества нашего VPN:</b>
• Невозможно заблокировать (маскируется под HTTPS)
• Высокая скорость без ограничений
• Поддержка всех устройств (iOS, Android, Windows, macOS)
• Один аккаунт = до 3 устройств одновременно

📱 <b>Как использовать:</b>
1. Нажмите "🛒 Купить VPN"
2. Выберите тариф и оплатите
3. Получите QR-код для мгновенной настройки
4. Или используйте ссылку для ручной настройки

❓ По всем вопросам: @support_username
    """
    
    await message.answer(
        welcome_text,
        reply_markup=main_menu(is_admin)
    )

@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    help_text = """
<b>❓ Частые вопросы:</b>

<b>Как подключиться?</b>
• Скачайте приложение TrustTunnel (скоро в App Store/Google Play)
• Или используйте любой клиент, поддерживающий наш протокол
• Отсканируйте QR-код из бота или введите конфигурацию вручную

<b>На сколько устройств?</b>
Один аккаунт работает на 3 устройствах одновременно.

<b>Что делать если не подключается?</b>
1. Проверьте интернет-соединение
2. Перезагрузите приложение
3. Обратитесь в поддержку: @support_username

<b>Как продлить подписку?</b>
Просто купите новый тариф - он добавится к существующему времени.
    """
    await message.answer(help_text)

@router.message(F.text == "📞 Поддержка")
async def cmd_support(message: Message):
    await message.answer(
        "📞 <b>Поддержка</b>\n\n"
        "Если у вас возникли проблемы или вопросы, напишите нам:\n"
        "@support_username\n\n"
        "Мы отвечаем ежедневно с 10:00 до 22:00 МСК."
    )