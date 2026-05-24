#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "Ошибка: Запустите деинсталлятор через sudo: sudo ./uninstall.sh"
  exit 1
fi

echo "=== Удаление KIPS (Kernel-level Intrusion Prevention System) ==="

echo "[*] Остановка фоновой службы kips..."
systemctl stop kips.service 2>/dev/null
systemctl disable kips.service 2>/dev/null

echo "[*] Удаление конфигурационных файлов systemd..."
rm -f /etc/systemd/system/kips.service
systemctl daemon-reload

echo "[*] Удаление файлов программы из /opt/kips..."
rm -rf /opt/kips

echo -n "Желаете удалить файл системных логов KIPS? (/var/log/kips.log) [y/N]: "
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    rm -f /var/log/kips.log
    echo "[+] Файл логов успешно удален."
else
    echo "[*] Файл логов сохранен для аудита безопасности."
fi

rm -f /usr/local/bin/kips-uninstall
echo "=== Деинсталляция KIPS успешно завершена! ==="
