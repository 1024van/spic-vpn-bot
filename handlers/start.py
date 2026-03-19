from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from database import db
from keyboards import main_menu, payment_methods
from config import ADMIN_IDS, PRICES
from handlers.purchase import PurchaseStates  # FSM покупки

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    # Регистрируем пользователя (без рефералок, как сейчас)
    db.add_user(user_id, username)
    is_admin = user_id in ADMIN_IDS

    # Разбираем аргумент /start
    args = message.text.split(maxsplit=1)
    arg = args[1] if len(args) == 2 else ""

    # Коды тарифов, приходящие с сайта
    plan_code = None

    if arg == "plan_1m":
        plan_code = "1_month"
    elif arg == "plan_3m":
        plan_code = "3_months"
    elif arg == "plan_6m":
        plan_code = "6_months"
    elif arg == "plan_12m":
        plan_code = "12_months"

    # Если передан валидный план — сразу открываем подтверждение заказа и выбор оплаты
    if plan_code and plan_code in PRICES:
        plan = PRICES[plan_code]

        await state.set_state(PurchaseStates.confirming_payment)
        await state.update_data(
            plan_code=plan_code,
            price=plan["price"],
            days=plan["days"],
            label=plan["label"],
        )

        text = (
            "📦 <b>Подтверждение заказа SPIC:</b>\n\n"
            f"• Тариф: {plan['label']}\n"
            f"• Период: {plan['days']} дней\n"
            "• Сервер: 🌍 Европа (stop2virus.xyz)\n"
            f"• Сумма: <b>{plan['price']}₽</b>\n\n"
            "Выберите способ оплаты:"
        )

        await message.answer(text, reply_markup=payment_methods())
        return

    # Обычный старт без параметров
        welcome_text = (
            "👋 Добро пожаловать в <b>Secure Protected Internet Connection</b>!\n"
            "🔒 <b>Преимущества нашего SPIC:</b>\n"
            "• Невозможно заблокировать (маскируется под HTTPS)\n"
            "• Высокая скорость без ограничений\n"
            "• Поддержка всех устройств (iOS, Android, Windows, macOS)\n"
            "• Один аккаунт = до 3 устройств одновременно\n\n"
            "📱 <b>Как использовать:</b>\n"
            "1. Нажмите \"🛒 Купить SPIC\"\n"
            "2. Выберите тариф и оплатите\n"
            "3. Получите QR-код для мгновенной настройки\n"
            "4. Или используйте ссылку для ручной настройки\n\n"
            "❓ По всем вопросам: @support_username\n"
        )

    await message.answer(
        welcome_text,
        reply_markup=main_menu(is_admin),
    )
