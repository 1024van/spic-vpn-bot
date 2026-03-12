cat > /opt/vpn_bot/README.md << 'EOF'
# SPIC - Secure Protected Internet Connection

![SPIC Logo](https://stop2virus.xyz/logo.png)

Telegram-бот для продажи VPN-подписок на базе протокола **TrustTunnel**.

## 🚀 Особенности

- **Невозможно заблокировать** — трафик маскируется под HTTPS
- **Высокая скорость** — до 1 Гбит/с без ограничений
- **До 3 устройств** одновременно
- **Мгновенная настройка** — QR-код и deep-link
- **Автоматическая оплата** — интеграция с FreeKassa

## 📋 Тарифы

| Тариф | Период | Цена |
|-------|--------|------|
| SPIC Basic | 1 месяц | 299₽ |
| SPIC Standard | 3 месяца | 799₽ |
| SPIC Pro | 6 месяцев | 1499₽ |
| SPIC Ultimate | 12 месяцев | 2499₽ |

## 🛠 Технологии

- **Python 3.12** + aiogram 3.x
- **TrustTunnel** — современный VPN протокол от AdGuard
- **FreeKassa** — платёжная система
- **SQLite** — база данных
- **systemd** — управление сервисами

## 📦 Установка

```bash
# Клонирование
git clone https://github.com/1024van/spic-vpn-bot.git
cd spic-vpn-bot

# Настройка окружения
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Конфигурация
cp .env.example .env
nano .env  # Заполни токены

# Запуск
python bot.py
⚙️ Systemd сервис
bash
Copy
sudo cp spic-bot.service /etc/systemd/system/
sudo systemctl enable spic-bot --now
🔒 Безопасность
fail2ban защита SSH
Только key-based аутентификация
Автоматические бэкапы базы данных
📞 Поддержка
Telegram: @spic_support
Сайт: https://stop2virus.xyz
📄 Лицензия
MIT License — см. LICENSE
SPIC — ваш защищённый интернет без границ.
EOF
plain
Copy

### 2. .gitignore

```bash
cat > /opt/vpn_bot/.gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/
log/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Bot specific
bot.session
*.session
backups/

# Keys and secrets
*.pem
*.key
id_*
!id_*.pub

# Temporary files
tmp/
temp/
.cache/
EOF
