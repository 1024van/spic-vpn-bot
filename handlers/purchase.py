from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import subscription_plans, payment_methods, main_menu, freekassa_payment_url
from config import PRICES, ADMIN_IDS, FREEKASSA_ENABLED, SITE_BASE_URL
from utils.trusttunnel import trusttunnel
from utils.payments import freekassa

from cloudpayments_client import get_public_id  # пока не используем, но пригодится

import base64
from datetime import datetime
import os

router = Router()

class PurchaseStates(StatesGroup):
    selecting_plan = State()
    confirming_payment = State()
    waiting_payment = State()

# ==============================
#        Хендлеры покупок
# ==============================


@router.message(F.text == "🛒 Купить SPIC")
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
        reply_markup=subscription_plans(),
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
        f"📦 <b>Подтверждение заказа SPIC:</b>\n\n"
        f"• Тариф: {plan_data['label']}\n"
        f"• Период: {plan_data['days']} дней\n"
        f"• Сервер: 🌍 Европа (stop2virus.xyz)\n"
        f"• Сумма: <b>{plan_data['price']}₽</b>\n\n"
        f"Выберите способ оплаты:",
        reply_markup=payment_methods(),
    )
    await state.set_state(PurchaseStates.confirming_payment)
    await callback.answer()


@router.callback_query(PurchaseStates.confirming_payment, F.data.startswith("pay_"))
@router.callback_query(PurchaseStates.confirming_payment, F.data.startswith("pay_"))
async def process_payment_selection(callback: CallbackQuery, state: FSMContext, bot: Bot):
    payment_method = callback.data.replace("pay_", "")
    data = await state.get_data()
    user_id = callback.from_user.id

    # Ручная оплата
    if payment_method == "manual":
        await callback.message.edit_text(
            "💬 <b>Ручная оплата</b>\n\n"
            "Напишите администратору для оплаты:\n"
            f"@{callback.from_user.username or 'admin'}\n\n"
            f"Укажите сумму: <b>{data['price']}₽</b>\n"
            f"Тариф: {data['label']}\n\n"
            f"После оплаты админ выдаст подписку командой:\n"
            f"<code>/confirm {data['order_id'] if 'order_id' in data else 'ORDER_ID'}</code>",
            parse_mode="HTML",
        )
        await state.clear()
        await callback.answer()
        return

    # Новый метод: CloudPayments (карта / СБП)
    if payment_method == "cp":
        # генерируем order_id
        order_id = f"SPIC_CP_{user_id}_{int(datetime.now().timestamp())}"

        # сохраняем платёж в БД
        db.add_payment(user_id, data["price"], order_id, data["plan_code"])

        price = data["price"]
        pay_url = f"{SITE_BASE_URL}/pay/cloudpayments?order_id={order_id}&amount={price}&uid={user_id}"

        await callback.message.edit_text(
            "💳 <b>Оплата картой / СБП (CloudPayments)</b>\n\n"
            f"Сумма: <b>{data['price']}₽</b>\n"
            f"Номер заказа: <code>{order_id}</code>\n\n"
            "Нажмите кнопку ниже для перехода к оплате.\n"
            "После успешной оплаты подписка будет выдана автоматически "
            "(или админ подтвердит командой /confirm).",
            reply_markup=freekassa_payment_url(pay_url),  # используем ту же кнопку "Перейти к оплате"
            parse_mode="HTML",
        )

        # Можно сохранить order_id в стейт, если пригодится
        await state.update_data(order_id=order_id)
        await callback.answer()
        return

    # Старый метод: FreeKassa
    if payment_method == "freekassa" and FREEKASSA_ENABLED:
        order_id = f"SPIC_{user_id}_{int(datetime.now().timestamp())}"

        db.add_payment(user_id, data["price"], order_id, data["plan_code"])

        print(
            f"DEBUG: FreeKassa pay handler, user_id={user_id}, "
            f"plan={data['plan_code']}, price={data['price']}, order_id={order_id}"
        )

        payment_url = freekassa.create_payment_url(
            amount=data["price"],
            order_id=order_id,
        )

        print("DEBUG: FreeKassa URL:", payment_url)

        await callback.message.edit_text(
            f"💳 <b>Оплата через FreeKassa</b>\n\n"
            f"Сумма: <b>{data['price']}₽</b>\n"
            f"Номер заказа: <code>{order_id}</code>\n\n"
            f"Нажмите кнопку ниже для перехода к оплате.\n"
            f"После оплаты нажмите «Я оплатил».",
            reply_markup=freekassa_payment_url(payment_url),
            parse_mode="HTML",
        )

        await state.set_state(PurchaseStates.waiting_payment)
        await state.update_data(order_id=order_id)
        await callback.answer()
        return

    await callback.answer("❌ Способ оплаты недоступен", show_alert=True)


@router.callback_query(PurchaseStates.waiting_payment, F.data == "check_payment")
async def check_payment_status(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Проверка статуса платежа FreeKassa (ручная)"""
    data = await state.get_data()
    user_id = callback.from_user.id

    await callback.message.edit_text(
        "⏳ <b>Проверка платежа...</b>\n\n"
        "Если вы уже оплатили, администратор скоро подтвердит платёж.\n"
        "Вы получите уведомление когда подписка будет активирована."
    )

    from config import ADMIN_IDS  # чтобы не тянуть глобально наверх

    for admin_id in ADMIN_IDS:
        await bot.send_message(
            admin_id,
            f"💳 <b>Новый платёж на проверке (FreeKassa)!</b>\n\n"
            f"Пользователь: {user_id}\n"
            f"Заказ: {data.get('order_id', 'N/A')}\n\n"
            f"Проверьте в <a href='https://freekassa.ru/cabinet/merchant'>кабинете FreeKassa</a>\n"
            f"и подтвердите командой:\n"
            f"<code>/confirm {data.get('order_id', 'N/A')}</code>",
            disable_web_page_preview=True,
        )

    await state.clear()
    await callback.answer()


@router.message(F.text == "📱 Мои подписки")
async def my_subscriptions(message: Message):
    user_id = message.from_user.id
    subs = db.get_active_subscriptions(user_id)
    balance = db.get_balance(user_id)

    if not subs:
        await message.answer(
            "📱 <b>У вас нет активных подписок</b>\n\n"
            f"💰 Ваш реферальный баланс: <b>{balance}₽</b>\n\n"
            "Нажмите '🛒 Купить SPIC' чтобы приобрести доступ.",
            reply_markup=main_menu(user_id in ADMIN_IDS),
        )
        return

    text = "📱 <b>Ваши активные подписки SPIC:</b>\n\n"

    for sub in subs:
        days_left = (sub["expires_at"] - datetime.now()).days
        text += (
            f"• Сервер: {sub['server']}\n"
            f"• Логин: <code>{sub['username']}</code>\n"
            f"• Истекает: {sub['expires_at'].strftime('%d.%m.%Y')} "
            f"(осталось {days_left} дней)\n\n"
        )

    text += f"💰 Ваш реферальный баланс: <b>{balance}₽</b>\n\n"
    text += "Для продления просто купите новый тариф."

    await message.answer(text, reply_markup=main_menu(user_id in ADMIN_IDS))


@router.message(Command("confirm"))
async def confirm_payment_manual(message: Message, bot: Bot):
    """Админ подтверждает платеж вручную"""
    from config import ADMIN_IDS

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

        if payment["status"] == "completed":
            await message.reply("⚠️ Этот платеж уже подтвержден")
            return

        db.confirm_payment(order_id)

        await deliver_subscription(
            bot,
            payment["user_id"],
            payment["plan_code"],
            payment_id=order_id,
            amount=payment["amount"],
        )

        await message.reply(f"✅ Платеж {order_id} подтвержден. Подписка выдана.")

    except Exception as e:
        await message.reply(f"❌ Ошибка: {str(e)}")


async def deliver_subscription(bot: Bot, user_id: int, plan_code: str, payment_id: str, amount: int):
    """Выдача подписки после оплаты + реферальное вознаграждение"""
    from config import ADMIN_IDS

    try:
        plan_data = PRICES[plan_code]

        config = trusttunnel.create_user(user_id)

        expires_at = db.add_subscription(
            user_id,
            config["username"],
            "MAIN",
            plan_data["days"],
            config,
        )

        ref_link = f"https://t.me/SpichText_bot?start=ref_{user_id}"

        text = f"""✅ <b>Поздравляем! Доступ готов!</b>

📍 Локация: 🇫🇮 FIN (Финляндия)

📱 <b>Мобильные устройства (iOS / Android):</b>
🍏 App Store: [https://apps.apple.com/us/app/trusttunnel/id6755807890](https://apps.apple.com/us/app/trusttunnel/id6755807890)
🤖 Google Play: [https://play.google.com/store/apps/details?id=com.adguard.trusttunnel](https://play.google.com/store/apps/details?id=com.adguard.trusttunnel)
━━━━━━━━━━━━━━━
📝 <b>Скопируйте эти данные в приложение:</b>

🏷 Server name: <code>SPIC_FIN</code>
🏘 IP address... : <code>185.236.24.249:443</code>
🌐 Domain name...: <code>stop2virus.xyz</code>
👤 Username: <code>{config['username']}</code>
🔑 Password: <code>{config.get('password', '******')}</code>
⚙️ Protocol: QUIC
📂 Routing profile: Default profile

⏳ Подписка активна до: <b>{expires_at.strftime('%d.%m.%Y')}</b>

🛡 DNS server addresses (нажми для копирования сразу обоих):
<code>https://dns.adguard-dns.com/dns-query</code>
<code>quic://dns.adguard-dns.com</code>
━━━━━━━━━━━━━━━
👥 <b>Реферальная программа</b>
Приглашайте друзей и получайте <b>30% от каждой их оплаты</b> на внутренний баланс.

Ваша ссылка:
<code>{ref_link}</code>
━━━━━━━━━━━━━━━
🖥  <b>Для пользователей ПК (Windows/Mac):</b>
Используйте прикреплённый файл .toml или QR/ссылку из сообщения ниже.
📖 Инструкции: WIN [https://trustunnel.ru/ttwinguide/](https://trustunnel.ru/ttwinguide/) | MAC [https://trustunnel.ru/ttmacguide/](https://trustunnel.ru/ttmacguide/)

📄 Terms: [https://trustunnel.ru/terms/](https://trustunnel.ru/terms/)
🔒 Privacy: [https://trustunnel.ru/privacy/](https://trustunnel.ru/privacy/)
💸 Refund: [https://trustunnel.ru/refund/](https://trustunnel.ru/refund/)
👨‍💻 Поддержка: [https://t.me/supTTbot](https://t.me/supTTbot)
"""

        await bot.send_message(
            user_id,
            text,
            parse_mode="HTML",
        )

        qr_bytes = base64.b64decode(config["qr_code"])
        photo = BufferedInputFile(qr_bytes, filename="qr_code.png")

        await bot.send_photo(
            user_id,
            photo=photo,
            caption=(
                "📱 Можете просто отсканировать этот QR-код в приложении TrustTunnel.\n\n"
                "🔗 Или используйте ссылку:\n"
                f"<code>{config['deeplink']}</code>"
            ),
            parse_mode="HTML",
        )

        # Отдельное сообщение с реферальной ссылкой
        await bot.send_message(
            user_id,
            "🔗 <b>Ваша реферальная ссылка:</b>\n"
            f"<code>{ref_link}</code>",
            parse_mode="HTML",
        )

        referrer_id = db.get_referrer(user_id)
        if referrer_id:
            reward = int(amount * 0.3)
            if reward > 0:
                db.add_referral_reward(
                    referrer_id=referrer_id,
                    referred_user_id=user_id,
                    payment_id=payment_id,
                    reward_amount=reward,
                )
                new_balance = db.get_balance(referrer_id)
                await bot.send_message(
                    referrer_id,
                    f"🎉 Ваш реферал <code>{user_id}</code> оплатил подписку на {amount}₽.\n"
                    f"Мы начислили вам <b>{reward}₽</b> на реферальный баланс.\n"
                    f"Текущий баланс: <b>{new_balance}₽</b>.",
                    parse_mode="HTML",
                )

        await bot.send_message(
            user_id,
            (
                "📥 <b>Если приложение ещё не установлено:</b>\n\n"
                "• <b>iOS:</b> TrustTunnel в App Store\n"
                "• <b>Android:</b> TrustTunnel в Google Play\n\n"
                "❓ По вопросам обращайтесь в поддержку."
            ),
            parse_mode="HTML",
            reply_markup=main_menu(user_id in ADMIN_IDS),
        )

    except Exception as e:
        await bot.send_message(
            user_id,
            f"❌ <b>Ошибка создания конфигурации:</b>\n{str(e)}\n\n"
            f"Обратитесь в поддержку.",
            parse_mode="HTML",
        )

        for admin_id in ADMIN_IDS:
            await bot.send_message(
                admin_id,
                f"🚨 <b>Ошибка выдачи подписки!</b>\n"
                f"User ID: {user_id}\n"
                f"Error: {str(e)}",
                parse_mode="HTML",
            )


def register_handlers_purchase(dp):
    dp.include_router(router)
