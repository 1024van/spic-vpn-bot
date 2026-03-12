from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def main_menu(is_admin: bool = False):
    builder = ReplyKeyboardBuilder()
    builder.button(text="🛒 Купить VPN")
    builder.button(text="📱 Мои подписки")
    builder.button(text="❓ Помощь")
    builder.button(text="📞 Поддержка")
    
    if is_admin:
        builder.button(text="🔐 Админ-панель")
    
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def subscription_plans():
    builder = InlineKeyboardBuilder()
    builder.button(text="1 месяц - 299₽", callback_data="buy_1_month")
    builder.button(text="3 месяца - 799₽", callback_data="buy_3_months")
    builder.button(text="6 месяцев - 1499₽", callback_data="buy_6_months")
    builder.button(text="12 месяцев - 2499₽", callback_data="buy_12_months")
    builder.adjust(1)
    return builder.as_markup()

def payment_methods():
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Банковская карта", callback_data="pay_card")
    builder.button(text="🔄 Криптовалюта (USDT)", callback_data="pay_crypto")
    builder.button(text="💬 Написать админу", callback_data="pay_manual")
    builder.adjust(1)
    return builder.as_markup()

def admin_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📊 Статистика")
    builder.button(text="👥 Пользователи")
    builder.button(text="🔄 Перезапустить Endpoint")
    builder.button(text="⬅️ Назад")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)