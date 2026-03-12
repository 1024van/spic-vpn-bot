from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    BufferedInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards import subscription_plans, payment_methods, main_menu
from config import PRICES, ADMIN_IDS, YOOMONEY_RECEIVER, YOOMONEY_TARGETS
from utils.trusttunnel import trusttunnel
from urllib.parse import urlencode
import uuid
import base64
from datetime import datetime


router = Router()


class PurchaseStates(StatesGroup):
    selecting_plan = State()
    confirming_payment = State()


def build_yoomoney_url(plan_code: str, user_id: int, price: int) -> str:
    """Собирает ссылку на оплату через ЮMoney quickpay."""
    label = f"tg_{user_id}_{plan_code}"
    targets = YOOMONEY_TARGETS.get(plan_code, f"Оплата тарифа {plan_code}")
    params = {
        "receiver": YOOMONEY_RECEIVER,
        "quickpay-form": "shop",
        "targets": targets,
        "sum": price,
        "paymentType": "AC",  # оплата картой
        "label": label,
    }
    return "https://yoomoney.ru/quickpay/confirm.xml?" + urlencode(params)


@router.message(F.text.contains("Купить VPN"))
async def buy_vpn(message: Message):
    await message.answer(
        "📋 Выберите тарифный план:\n\n"
        "⚡ Все тарифы включают:\n"
        "• Неограниченный трафик\n"
        "• Скорость до 1 Гбит/с\n"
        "• До 3 устройств одновременно\n"
        "• Доступ ко всем серверам",
        reply_markup=subscription_plans(),
        parse_mode=None,
    )


@router.callback_query(F.data.startswith("buy_"))
async def process_plan_selection(callback: CallbackQuery, state: FSMContext):
    plan_code = callback.data.replace("buy_", "")
    plan_data = PRICES.get(plan_code)

    if not plan_data:
        await callback.answer("❌ Ошибка выбора плана", show_alert=True)
        return

    await state.update_data(
        plan_code=plan_code,
        price=plan_data["price"],
        days=plan_data["days"],
        label=plan_data["label"],
    )

    await callback.message.edit_text(
        "📦 Подтверждение заказа:\n\n"
        f"• Тариф: {plan_data['label']}\n"
        f"• Период: {plan_data['days']} дней\n"
        "• Сервер: 🌍 Основной (stop2virus.xyz)\n"
        f"• Сумма: {plan_data['price']}₽\n\n"
        "Выберите способ оплаты:",
        reply_markup=payment_methods(),
        parse_mode=None,
    )
    await state.set_state(PurchaseStates.confirming_payment)
    await callback.answer()


@router.callback_query(PurchaseStates.confirming_payment, F.data.startswith("pay_"))
async def process_payment_selection(callback: CallbackQuery, state: FSMContext, bot: Bot):
    payment_method = callback.data.replace("pay_", "")
    data = await state.get_data()
    user_id = callback.from_user.id

    if payment_method == "manual":
        await callback.message.edit_text(
            "💬 Ручная оплата\n\n"
            "Напишите администратору для оплаты:\n"
            f"@{callback.from_user.username or 'admin'}\n\n"
            f"Укажите сумму: {data['price']}₽\n"
            f"Тариф: {data['label']}",
            parse_mode=None,
        )
        await state.clear()
        return

    # Генерируем ID платежа и сохраняем в БД
    payment_id = str(uuid.uuid4())[:8]
    db.add_payment(user_id, data["price"], payment_id, data["plan_code"])

    if payment_method == "card":
        # ЮMoney quickpay-кнопка
        pay_url = build_yoomoney_url(
            data["plan_code"],
            user_id,
            data["price"],
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"Оплатить {data['price']}₽ через ЮMoney",
                        url=pay_url,
                    )
                ]
            ]
        )

        await callback.message.edit_text(
            "💳 Оплата картой через ЮMoney\n\n"
            f"Сумма: {data['price']}₽\n"
            f"Номер заказа: {payment_id}\n\n"
            "Нажмите кнопку ниже, чтобы перейти на страницу оплаты.\n\n"
            "После оплаты отправьте чек/скриншот администратору.\n"
            "Админ подтвердит платеж командой:\n"
            f"/confirm {payment_id}",
            reply_markup=kb,
            parse_mode=None,
        )

    elif payment_method == "crypto":
        await callback.message.edit_text(
            "🔄 Оплата криптовалютой\n\n"
            f"Сумма: {data['price']}₽ (~{data['price']/90:.2f} USDT)\n"
            f"Номер заказа: {payment_id}\n\n"
            "Адрес для оплаты:\n"
            "0x1234567890abcdef...\n\n"
            "После оплаты отправьте скриншот админу.",
            parse_mode=None,
        )

    await state.clear()
    await callback.answer()


@router.message(F.text == "📱 Мои подписки")
async def my_subscriptions(message: Message):
    user_id = message.from_user.id
    subs = db.get_active_subscriptions(user_id)

    if not subs:
        await message.answer(
            "📱 У вас нет активных подписок\n\n"
            "Нажмите '🛒 Купить VPN' чтобы приобрести доступ.",
            reply_markup=main_menu(user_id in ADMIN_IDS),
            parse_mode=None,
        )
        return

    text = "📱 Ваши активные подписки:\n\n"

    for sub in subs:
        days_left = (sub["expires_at"] - datetime.now()).days
        text += (
            f"• Сервер: {sub['server']}\n"
            f"• Логин: {sub['username']}\n"
            f"• Истекает: {sub['expires_at'].strftime('%d.%m.%Y')} "
            f"(осталось {days_left} дней)\n\n"
        )

    text += "Для продления просто купите новый тариф."

    await message.answer(text, parse_mode=None)


@router.message(Command("confirm"))
async def confirm_payment_manual(message: Message, bot: Bot):
    from config import ADMIN_IDS

    await message.reply(
        f"debug: /confirm от {message.from_user.id}, ADMIN_IDS={ADMIN_IDS}",
        parse_mode=None,
    )

    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        args = message.text.split()
        if len(args) != 2:
            await message.reply("Использование: /confirm <payment_id>", parse_mode=None)
            return

        payment_id = args[1]

        payment = db.get_payment(payment_id)
        if not payment:
            await message.reply("Платеж не найден", parse_mode=None)
            return

        if payment["status"] == "completed":
            await message.reply("Этот платеж уже подтвержден", parse_mode=None)
            return

        # Подтверждаем платеж
        db.confirm_payment(payment_id)

        # Выдаем подписку
        await deliver_subscription(
            bot,
            payment["user_id"],
            payment["plan_code"],
        )

        await message.reply(
            f"Платеж {payment_id} подтвержден. Подписка выдана.",
            parse_mode=None,
        )

    except Exception as e:
        text = f"Ошибка в /confirm: {type(e).__name__}: {e}"
        await message.answer(text, parse_mode=None)


async def deliver_subscription(bot: Bot, user_id: int, plan_code: str):
    """Выдача подписки после оплаты"""
    try:
        plan_data = PRICES[plan_code]

        # Создаем пользователя в TrustTunnel
        config = trusttunnel.create_user(user_id)

        # Сохраняем в БД
        expires_at = db.add_subscription(
            user_id,
            config["username"],
            "MAIN",
            plan_data["days"],
            config,
        )

        # Отправляем QR-код
        qr_bytes = base64.b64decode(config["qr_code"])
        photo = BufferedInputFile(qr_bytes, filename="qr_code.png")

        caption = (
            "🎉 Ваша подписка активирована!\n\n"
            f"Сервер: stop2virus.xyz\n"
            f"Активна до: {expires_at.strftime('%d.%m.%Y')}\n"
            f"Логин: {config['username']}\n\n"
            "Быстрая настройка:\n"
            "1. Установите приложение TrustTunnel\n"
            "2. Отсканируйте QR-код выше\n"
            "3. Готово!\n\n"
            "Или используйте ссылку:\n"
            f"{config['deeplink']}"
        )

        await bot.send_photo(
            user_id,
            photo=photo,
            caption=caption,
            parse_mode=None,
        )

        # Отправляем инструкцию (без HTML-парсинга)
        text = (
            "📥 Скачать приложение:\n\n"
            "• iOS: (скоро в App Store)\n"
            "• Android: (скоро в Google Play)\n"
            "• Windows/macOS/Linux:\n"
            "  https://github.com/TrustTunnel/TrustTunnelClient\n\n"
            "❓ По вопросам обращайтесь в поддержку."
        )
        await bot.send_message(
            user_id,
            text,
            reply_markup=main_menu(user_id in ADMIN_IDS),
            parse_mode=None,
        )

    except Exception as e:
        text = (
            "❌ Ошибка создания конфигурации:\n"
            f"{e}\n\n"
            "Обратитесь в поддержку."
        )
        await bot.send_message(
            user_id,
            text,
            parse_mode=None,
        )

        # Уведомляем админов с деталями (без HTML)
        for admin_id in ADMIN_IDS:
            admin_text = (
                "🚨 Ошибка выдачи подписки!\n"
                f"User ID: {user_id}\n"
                f"Plan: {plan_code}\n"
                f"Error type: {type(e).__name__}\n"
                f"Error: {e}"
            )
            await bot.send_message(
                admin_id,
                admin_text,
                parse_mode=None,
            )
