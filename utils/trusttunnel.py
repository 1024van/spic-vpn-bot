import subprocess
import os
import toml
import secrets
import qrcode
import io
import base64
from datetime import datetime
from typing import Dict
from config import (
    TRUSTTUNNEL_ENDPOINT_PATH,
    VPN_TOML,
    HOSTS_TOML,
    CREDENTIALS_TOML,
    TRUSTTUNNEL_PUBLIC_IP,
)


class TrustTunnelManager:
    def __init__(self):
        self.endpoint_path = TRUSTTUNNEL_ENDPOINT_PATH
        self.vpn_toml = VPN_TOML
        self.hosts_toml = HOSTS_TOML
        self.credentials_toml = CREDENTIALS_TOML
        self.public_ip = TRUSTTUNNEL_PUBLIC_IP

        # Проверяем наличие необходимых файлов
        if not os.path.exists(self.vpn_toml):
            raise FileNotFoundError(f"vpn.toml not found at {self.vpn_toml}")
        if not os.path.exists(self.hosts_toml):
            raise FileNotFoundError(f"hosts.toml not found at {self.hosts_toml}")

    def _generate_username(self, user_id: int) -> str:
        """Генерирует уникальное имя пользователя"""
        timestamp = int(datetime.now().timestamp())
        return f"user_{user_id}_{timestamp}"

    def _generate_password(self) -> str:
        """Генерирует случайный пароль"""
        return secrets.token_urlsafe(16)

    def _add_user_to_credentials(self, username: str, password: str):
        """Добавляет пользователя в credentials.toml"""
        # Читаем существующий файл или создаем новый
        if os.path.exists(self.credentials_toml):
            with open(self.credentials_toml, "r") as f:
                try:
                    data = toml.load(f)
                except Exception:
                    data = {}
        else:
            data = {}

        # Гарантируем, что есть ключ "client" как список
        if not isinstance(data, dict):
            data = {}
        clients = data.get("client")
        if not isinstance(clients, list):
            data["client"] = []
        # Добавляем нового пользователя
        data["client"].append(
            {
                "username": username,
                "password": password,
            }
        )

        # Сохраняем
        with open(self.credentials_toml, "w") as f:
            toml.dump(data, f)

        # Обновляем vpn.toml
        self._update_vpn_toml()

        return True

    def _update_vpn_toml(self):
        """Обновляет vpn.toml чтобы указать путь к credentials"""
        with open(self.vpn_toml, "r") as f:
            config = toml.load(f)

        config["credentials"] = self.credentials_toml

        with open(self.vpn_toml, "w") as f:
            toml.dump(config, f)

    def _generate_config(self, username: str) -> str:
        """Генерирует deeplink-конфигурацию для клиента через trusttunnel_endpoint"""
        cmd = [
            os.path.join(self.endpoint_path, "trusttunnel_endpoint"),
            self.vpn_toml,
            self.hosts_toml,
            "-c",
            username,
            "-a",
            self.public_ip,
            "--format",
            "deeplink",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.endpoint_path,
            )

            if result.returncode != 0:
                # Пробрасываем stderr, чтобы видеть причину
                raise Exception(f"Endpoint error: {result.stderr.strip()}")

            return result.stdout.strip()

        except Exception as e:
            raise Exception(f"Failed to generate config: {e}")

    def create_user(self, user_id: int) -> Dict:
        """
        Создает нового пользователя TrustTunnel.
        Возвращает данные для подключения.
        """
        username = self._generate_username(user_id)
        password = self._generate_password()

        # Добавляем в credentials
        self._add_user_to_credentials(username, password)

        # Перезапускаем endpoint чтобы применить изменения
        self._restart_endpoint()

        # Генерируем deeplink
        deeplink = self._generate_config(username)

        # Генерируем QR-код
        qr = qrcode.make(deeplink)
        img_buffer = io.BytesIO()
        qr.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        qr_base64 = base64.b64encode(img_buffer.read()).decode()

        return {
            "username": username,
            "password": password,
            "deeplink": deeplink,
            "qr_code": qr_base64,
        }

    def _restart_endpoint(self):
        """Перезапускает TrustTunnel endpoint"""
        try:
            # Определяем имя сервиса
            result = subprocess.run(
                ["systemctl", "list-units", "--type=service", "--state=running"],
                capture_output=True,
                text=True,
            )

            # Ищем сервис trusttunnel
            for line in result.stdout.split("\n"):
                if "trusttunnel" in line:
                    service_name = line.split()[0]
                    subprocess.run(
                        ["sudo", "systemctl", "restart", service_name],
                        check=False,
                        timeout=10,
                    )
                    return True

            # Если не нашли, пробуем стандартное имя
            subprocess.run(
                ["sudo", "systemctl", "restart", "trusttunnel"],
                check=False,
                timeout=10,
            )
            return True

        except Exception as e:
            print(f"Warning: Could not restart endpoint: {e}")
            return False

    def remove_user(self, username: str):
        """Удаляет пользователя"""
        if not os.path.exists(self.credentials_toml):
            return False

        with open(self.credentials_toml, "r") as f:
            data = toml.load(f)

        # Удаляем пользователя
        data["users"] = [u for u in data.get("users", []) if u.get("username") != username]

        with open(self.credentials_toml, "w") as f:
            toml.dump(data, f)

        self._restart_endpoint()
        return True


# Singleton
trusttunnel = TrustTunnelManager()
