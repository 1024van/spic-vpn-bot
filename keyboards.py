from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import FREEKASSA_ENABLED, YOOKASSA_ENABLED, PRICES

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
    
    for plan_code, plan_data in PRICES.items():
        label = plan_data["label"]
        if plan_data.get("savings"):
            label += f" | {plan_data['savings']}"
        builder.button(text=label, callback_data=f"buy_{plan_code}")
    
    builder.adjust(1)
    return builder.as_markup()

def payment_methods():
    builder = InlineKeyboardBuilder()
    
    # FreeKassa - основной метод
    if FREEKASSA_ENABLED:
        builder.button(text="💳 FreeKassa (Карты/Крипта)", callback_data="pay_freekassa")
    
    # ЮKassa - опционально
    if YOOKASSA_ENABLED:
        builder.button(text="💳 ЮKassa (Карты)", callback_data="pay_card")
    
    # Ручная оплата всегда доступна
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

def freekassa_payment_url(url: str):
    """Кнопка для перехода к оплате FreeKassa"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Перейти к оплате", url=url)
    builder.button(text="✅ Я оплатил", callback_data="check_payment")
    builder.adjust(1)
    return builder.as_markup()