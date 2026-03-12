from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards import subscription_plans, payment_methods, main_menu, freekassa_payment_url
from config import PRICES, ADMIN_IDS, FREEKASSA_ENABLED
from utils.trusttunnel import trusttunnel
from utils.payments import freekassa
import uuid
import base64
from datetime import datetime

router = Router()

class PurchaseStates(StatesGroup):
    selecting_plan = State()
    confirming_payment = State()
    waiting_payment = State()

@router.message(F.text == "🛒 Купить VPN")
async def buy_vpn(message: Message):
    await message.answer(
        "📋 <b>Выберите тариф SPIC:</b>\n\n"
        "🔒 <b>Secure Protected Internet Connection</b>\n\n"
        "⚡ Все тарифы включают:\n"
        "• Неограниченный трафик\n"
        "• Скорость до 1 Гбит/с\n"
        "• До 3 устройств одновременно\n"
        "• Протокол TrustTunnel (невозможно заблокировать)\n"
        "• Доступ к серверу в Европе",
        reply_markup=subscription_plans()
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
        label=plan_data["label"]
    )
    
    await callback.message.edit_text(
        f"📦 <b>Подтверждение заказа SPIC:</b>\n\n"
        f"• Тариф: {plan_data['label']}\n"
        f"• Период: {plan_data['days']} дней\n"
        f"• Сервер: 🌍 Европа (stop2virus.xyz)\n"
        f"• Сумма: <b>{plan_data['price']}₽</b>\n\n"
        f"Выберите способ оплаты:",
        reply_markup=payment_methods()
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
            "💬 <b>Ручная оплата</b>\n\n"
            "Напишите администратору для оплаты:\n"
            f"@{callback.from_user.username or 'admin'}\n\n"
            f"Укажите сумму: <b>{data['price']}₽</b>\n"
            f"Тариф: {data['label']}\n\n"
            f"После оплаты админ выдаст подписку командой:\n"
            f"<code>/confirm {user_id} {data['plan_code']}</code>"
        )
        await state.clear()
        return
    
    if payment_method == "freekassa" and FREEKASSA_ENABLED:
        # Генерируем ID заказа
        order_id = f"SPIC_{user_id}_{int(datetime.now().timestamp())}"
        
        # Сохраняем в БД
        db.add_payment(user_id, data['price'], order_id, data['plan_code'])
        
        # Создаём URL для оплаты
        payment_url = freekassa.create_payment_url(
            amount=data['price'],
            order_id=order_id,
            description=f"SPIC VPN {data['label']}"
        )
        
        await callback.message.edit_text(
            f"💳 <b>Оплата через FreeKassa</b>\n\n"
            f"Сумма: <b>{data['price']}₽</b>\n"
            f"Номер заказа: <code>{order_id}</code>\n\n"
            f"Нажмите кнопку ниже для перехода к оплате.\n"
            f"После оплаты нажмите «Я оплатил».",
            reply_markup=freekassa_payment_url(payment_url)
        )
        
        await state.set_state(PurchaseStates.waiting_payment)
        await state.update_data(order_id=order_id)
        await callback.answer()
        return
    
    await callback.answer("❌ Способ оплаты недоступен", show_alert=True)

@router.callback_query(PurchaseStates.waiting_payment, F.data == "check_payment")
async def check_payment_status(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Проверка статуса платежа (ручная, для демо)"""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    await callback.message.edit_text(
        "⏳ <b>Проверка платежа...</b>\n\n"
        "Если вы уже оплатили, администратор скоро подтвердит платёж.\n"
        "Вы получите уведомление когда подписка будет активирована."
    )
    
    # Уведомляем админов о новом платеже
    for admin_id in ADMIN_IDS:
        await bot.send_message(
            admin_id,
            f"💳 <b>Новый платёж на проверке!</b>\n\n"
            f"Пользователь: {user_id}\n"
            f"Заказ: {data.get('order_id', 'N/A')}\n\n"
            f"Проверьте в <a href='https://freekassa.ru/cabinet/merchant'>кабинете FreeKassa</a>\n"
            f"и подтвердите командой:\n"
            f"<code>/confirm {data.get('order_id', 'N/A')}</code>",
            disable_web_page_preview=True
        )
    
    await state.clear()
    await callback.answer()

@router.message(F.text == "📱 Мои подписки")
async def my_subscriptions(message: Message):
    user_id = message.from_user.id
    subs = db.get_active_subscriptions(user_id)
    
    if not subs:
        await message.answer(
            "📱 <b>У вас нет активных подписок</b>\n\n"
            "Нажмите '🛒 Купить VPN' чтобы приобрести доступ.",
            reply_markup=main_menu(user_id in ADMIN_IDS)
        )
        return
    
    text = "📱 <b>Ваши активные подписки SPIC:</b>\n\n"
    
    for sub in subs:
        days_left = (sub['expires_at'] - datetime.now()).days
        text += (
            f"• Сервер: {sub['server']}\n"
            f"• Логин: <code>{sub['username']}</code>\n"
            f"• Истекает: {sub['expires_at'].strftime('%d.%m.%Y')} "
            f"(осталось {days_left} дней)\n\n"
        )
    
    text += "Для продления просто купите новый тариф."
    
    await message.answer(text, reply_markup=main_menu(user_id in ADMIN_IDS))

@router.message(Command("confirm"))
async def confirm_payment_manual(message: Message, bot: Bot):
    """Админ подтверждает платеж вручную"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.reply("Использование: /confirm <order_id>")
            return
            
        order_id = args[1]
        payment = db.get_payment(order_id)
        
        if not payment:
            await message.reply("❌ Платеж не найден")
            return
        
        if payment['status'] == 'completed':
            await message.reply("⚠️ Этот платеж уже подтвержден")
            return
        
        # Подтверждаем платеж
        db.confirm_payment(order_id)
        
        # Выдаем подписку
        await deliver_subscription(
            bot,
            payment['user_id'],
            payment['plan_code']
        )
        
        await message.reply(f"✅ Платеж {order_id} подтвержден. Подписка выдана.")
        
    except Exception as e:
        await message.reply(f"❌ Ошибка: {str(e)}")

async def deliver_subscription(bot: Bot, user_id: int, plan_code: str):
    """Выдача подписки после оплаты"""
    try:
        plan_data = PRICES[plan_code]
        
        # Создаем пользователя в TrustTunnel
        config = trusttunnel.create_user(user_id)
        
        # Сохраняем в БД
        expires_at = db.add_subscription(
            user_id, 
            config['username'], 
            'MAIN', 
            plan_data['days'],
            config
        )
        
        # Отправляем QR-код
        qr_bytes = base64.b64decode(config['qr_code'])
        photo = BufferedInputFile(qr_bytes, filename="qr_code.png")
        
        await bot.send_photo(
            user_id,
            photo=photo,
            caption=(
                f"🎉 <b>Ваша подписка SPIC активирована!</b>\n\n"
                f"📍 Сервер: stop2virus.xyz\n"
                f"⏳ Активна до: {expires_at.strftime('%d.%m.%Y')}\n"
                f"👤 Логин: <code>{config['username']}</code>\n\n"
                f"📱 <b>Быстрая настройка:</b>\n"
                f"1. Установите приложение TrustTunnel\n"
                f"2. Отсканируйте QR-код выше\n"
                f"3. Готово!\n\n"
                f"🔗 <b>Или используйте ссылку:</b>\n"
                f"<code>{config['deeplink']}</code>"
            )
        )
        
        # Отправляем инструкцию
        await bot.send_message(
            user_id,
            (
                "📥 <b>Скачать приложение:</b>\n\n"
                "• <b>iOS:</b> (скоро в App Store)\n"
                "• <b>Android:</b> (скоро в Google Play)\n"
                "• <b>Windows/macOS/Linux:</b>\n"
                "https://github.com/TrustTunnel/TrustTunnelClient\n\n"
                "❓ По вопросам обращайтесь в поддержку."
            ),
            reply_markup=main_menu(user_id in ADMIN_IDS)
        )
        
    except Exception as e:
        await bot.send_message(
            user_id,
            f"❌ <b>Ошибка создания конфигурации:</b>\n{str(e)}\n\n"
            f"Обратитесь в поддержку."
        )
        
        # Уведомляем админов
        for admin_id in ADMIN_IDS:
            await bot.send_message(
                admin_id,
                f"🚨 <b>Ошибка выдачи подписки!</b>\n"
                f"User ID: {user_id}\n"
                f"Error: {str(e)}"
            )

def register_handlers_purchase(dp):
    dp.include_router(router)