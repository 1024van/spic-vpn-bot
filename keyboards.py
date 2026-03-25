from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import FREEKASSA_ENABLED, YOOKASSA_ENABLED, PRICES


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="🛒 Купить SPIC")
    builder.button(text="📱 Мои подписки")
    builder.button(text="❓ Помощь")
    builder.button(text="📞 Поддержка")

    if is_admin:
        builder.button(text="🔐 Админ-панель")

    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def subscription_plans() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for plan_code, plan_data in PRICES.items():
        label = plan_data["label"]
        if plan_data.get("savings"):
            label += f" | {plan_data['savings']}"
        builder.button(text=label, callback_data=f"buy_{plan_code}")

    builder.adjust(1)
    return builder.as_markup()


def payment_methods() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="💳 Картой / СБП (CloudPayments)",
                callback_data="pay_cp",
            )
        ],
    ]

    if FREEKASSA_ENABLED:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="💰 FreeKassa (кошелёк/крипта)",
                    callback_data="pay_freekassa",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="💬 Ручная оплата",
                callback_data="pay_manual",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📊 Статистика")
    builder.button(text="👥 Пользователи")
    builder.button(text="🔄 Перезапустить Endpoint")
    builder.button(text="⬅️ Назад")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def freekassa_payment_url(url: str) -> InlineKeyboardMarkup:
    """Кнопка для перехода к оплате FreeKassa"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Перейти к оплате", url=url)
    builder.button(text="✅ Я оплатил", callback_data="check_payment")
    builder.adjust(1)
    return builder.as_markup()


def tinkoff_payment_url(url: str) -> InlineKeyboardMarkup:
    """Кнопка для перехода к оплате Т‑Банк (пока не используется)"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Перейти к оплате (Т‑Банк)", url=url)
    builder.button(text="✅ Я оплатил", callback_data="check_payment_tinkoff")
    builder.adjust(1)
    return builder.as_markup()
