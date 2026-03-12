import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

# TrustTunnel настройки
TRUSTTUNNEL_ENDPOINT_PATH = os.getenv("TRUSTTUNNEL_ENDPOINT_PATH", "/opt/trusttunnel")
TRUSTTUNNEL_DOMAIN = os.getenv("TRUSTTUNNEL_DOMAIN", "stop2virus.xyz")
TRUSTTUNNEL_PUBLIC_IP = os.getenv("TRUSTTUNNEL_PUBLIC_IP")

# Проверяем что endpoint существует
if not os.path.exists(TRUSTTUNNEL_ENDPOINT_PATH):
    raise FileNotFoundError(f"TrustTunnel endpoint not found at {TRUSTTUNNEL_ENDPOINT_PATH}")

# Пути к файлам TrustTunnel
VPN_TOML = os.path.join(TRUSTTUNNEL_ENDPOINT_PATH, "vpn.toml")
HOSTS_TOML = os.path.join(TRUSTTUNNEL_ENDPOINT_PATH, "hosts.toml")
CREDENTIALS_TOML = os.path.join(TRUSTTUNNEL_ENDPOINT_PATH, "credentials.toml")

# Цены (в рублях) - обновлены по сайту stop2virus.xyz
PRICES = {
    "1_month": {
        "price": 299, 
        "days": 30, 
        "label": "1 месяц — 299 ₽",
        "savings": None,
        "freekassa_id": "1"
    },
    "3_months": {
        "price": 599, 
        "days": 90, 
        "label": "3 месяца — 599 ₽ (~200 ₽/мес)",
        "savings": "Экономия 298 ₽",
        "freekassa_id": "2"
    },
    "6_months": {
        "price": 899, 
        "days": 180, 
        "label": "6 месяцев — 899 ₽ (~150 ₽/мес)", 
        "savings": "Экономия 895 ₽",
        "freekassa_id": "3"
    },
    "12_months": {
        "price": 1199, 
        "days": 365, 
        "label": "12 месяцев — 1199 ₽ (~100 ₽/мес)",
        "savings": "Экономия 2389 ₽",
        "freekassa_id": "4"
    }
}

# FreeKassa настройки (основной платёжный метод)
FREEKASSA_ENABLED = os.getenv("FREEKASSA_ENABLED", "true").lower() == "true"
FREEKASSA_MERCHANT_ID = os.getenv("FREEKASSA_MERCHANT_ID", "")
FREEKASSA_SECRET1 = os.getenv("FREEKASSA_SECRET1", "")
FREEKASSA_SECRET2 = os.getenv("FREEKASSA_SECRET2", "")

# ЮKassa (опционально, отключена по умолчанию)
YOOKASSA_ENABLED = os.getenv("YOOKASSA_ENABLED", "false").lower() == "true"
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")

# ЮMoney (полностью отключена, но можно включить изменив код)
YMONEY_ENABLED = False

# Сервер (у нас пока один)
VPN_SERVER = {
    "code": "MAIN",
    "name": "🌍 Основной сервер",
    "domain": TRUSTTUNNEL_DOMAIN,
    "location": "EU"
}