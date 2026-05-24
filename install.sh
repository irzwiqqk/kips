#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "Ошибка: Запустите скрипт через sudo: sudo ./install.sh"
  exit 1
fi

echo "=== Установка KIPS (Kernel-level Intrusion Prevention System) ==="

INSTALL_DIR="/opt/kips"
mkdir -p "$INSTALL_DIR"

echo "[*] Сканирование текущих устройств для белого списка..."
WHITELIST_FILE="$INSTALL_DIR/whitelist.txt"
touch "$WHITELIST_FILE"

for serial_path in /sys/bus/usb/devices/*/serial; do
    if [ -f "$serial_path" ]; then
        serial_val=$(cat "$serial_path")
        if [ ! -z "$serial_val" ] && ! grep -q "$serial_val" "$WHITELIST_FILE"; then
            echo "$serial_val" >> "$WHITELIST_FILE"
            echo "    [+] В белый список добавлен S/N: $serial_val"
        fi
    fi
done

if [ -f "kips.py" ]; then
    cp kips.py "$INSTALL_DIR/kips.py"
    chmod +x "$INSTALL_DIR/kips.py"
    echo "[+] Файлы KIPS скопированы в $INSTALL_DIR"
else
    echo "[-] Ошибка: файл kips.py не найден в текущей папке!"
    exit 1
fi

touch /var/log/kips.log
chmod 640 /var/log/kips.log
echo "[+] Файл логов подготовлен (/var/log/kips.log)"

SERVICE_FILE="/etc/systemd/system/kips.service"

echo "[Unit]
Description=KIPS USB Intrusion Prevention System
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 $INSTALL_DIR/kips.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target" > "$SERVICE_FILE"

echo "[+] Юнит systemd успешно создан"

systemctl daemon-reload
systemctl enable kips.service
systemctl start kips.service

# Создаем глобальную команду удаления
cp uninstall.sh "$INSTALL_DIR/uninstall.sh"
chmod +x "$INSTALL_DIR/uninstall.sh"
ln -sf "$INSTALL_DIR/uninstall.sh" /usr/local/bin/kips-uninstall

echo "=== Установка KIPS успешно завершена! ==="
echo "Ваша мышь и клавиатура защищены белым списком."
echo "Удалить софт из любой папки: sudo kips-uninstall"
echo "Логи в реальном времени: tail -f /var/log/kips.log"
