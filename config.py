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

# Цены (в рублях)
PRICES = {
    "1_month": {"price": 299, "days": 30, "label": "1 месяц - 299₽"},
    "3_months": {"price": 799, "days": 90, "label": "3 месяца - 799₽"},
    "6_months": {"price": 1499, "days": 180, "label": "6 месяцев - 1499₽"},
    "12_months": {"price": 2499, "days": 365, "label": "12 месяцев - 2499₽"}
}

# ЮMoney
YOOMONEY_RECEIVER = "4100119484107963"

YOOMONEY_TARGETS = {
    "1_month":  "Тариф 1 месяц",
    "3_months": "Тариф 3 месяца",
    "6_months": "Тариф 6 месяцев",
    "12_months":"Тариф 12 месяцев",
}
# Если хочешь, можешь не дублировать цены, а брать из PRICES

# Сервер (у нас пока один)
VPN_SERVER = {
    "code": "MAIN",
    "name": "🌍 Основной сервер",
    "domain": TRUSTTUNNEL_DOMAIN,
    "location": "EU"
}
