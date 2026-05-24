import subprocess
import os
from datetime import datetime

LOG_FILE = "/var/log/kips.log"
WHITELIST_FILE = "/opt/kips/whitelist.txt"

def get_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        return ["No Serial"]
    with open(WHITELIST_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)
    print(log_entry.strip())

def disconnect_usb(usb_bus_id, serial):
    if not usb_bus_id:
        return
    whitelist = get_whitelist()
    if serial in whitelist or serial == "No Serial":
        log_event(f"[INFO] Устройство {serial} в белом списке. Доступ разрешен.")
        return
    log_event(f"[SENSITIVE] АКТИВНАЯ ЗАЩИТА KIPS: Недоверенное устройство! Блокировка порта {usb_bus_id}...")
    cmd = f"echo '{usb_bus_id}' > /sys/bus/usb/drivers/usb/unbind"
    try:
        os.system(cmd)
        log_event(f"[SUCCESS] Порт {usb_bus_id} успешно изолирован.")
    except Exception as e:
        log_event(f"[ERROR] Не удалось отключить порт: {e}")

def monitor_usb():
    log_event("KIPS: Мониторинг ядерных событий запущен.")
    process = subprocess.Popen(
        ["udevadm", "monitor", "--environment", "--subsystem=usb"],
        stdout=subprocess.PIPE,
        text=True
    )
    current_device = {}
    for line in process.stdout:
        line = line.strip()
        if "ACTION=add" in line:
            current_device["action"] = "ПОДКЛЮЧЕНИЕ"
        elif "ACTION=remove" in line:
            current_device["action"] = "ОТКЛЮЧЕНИЕ"
        if "DEVPATH=" in line:
            current_device["bus_id"] = line.split("/")[-1]
        if "ID_VENDOR=" in line:
            current_device["vendor"] = line.split("=")[1]
        if "ID_MODEL=" in line:
            current_device["model"] = line.split("=")[1]
        if "ID_SERIAL=" in line:
            current_device["serial"] = line.split("=")[1]
        if line == "" and current_device:
            action = current_device.get("action", "UNKNOWN")
            vendor = current_device.get("vendor", "Unknown Vendor")
            model = current_device.get("model", "Unknown Model")
            serial = current_device.get("serial", "No Serial")
            bus_id = current_device.get("bus_id", None)
            if action == "ПОДКЛЮЧЕНИЕ":
                msg = f"[ALERT] {action} -> {vendor} {model} | S/N: {serial} | Порт: {bus_id}"
                log_event(msg)
                if bus_id:
                    disconnect_usb(bus_id, serial)
            elif action == "ОТКЛЮЧЕНИЕ":
                msg = f"[INFO] {action} -> Порт {bus_id} освобожден."
                log_event(msg)
            current_device = {}

if __name__ == "__main__":
    try:
        monitor_usb()
    except KeyboardInterrupt:
        log_event("KIPS: Мониторинг остановлен.")
    except Exception as e:
        log_event(f"KIPS: Критическая ошибка: {e}")
