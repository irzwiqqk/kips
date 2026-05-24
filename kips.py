import subprocess
import os
import time
from datetime import datetime

LOG_FILE = "/var/log/kips.log"
WHITELIST_FILE = "/opt/kips/whitelist.txt"

BANNED_PORTS = {}
BAN_TIMEOUT = 30  

def get_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        return []
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
        
    current_time = time.time()
    base_port = usb_bus_id.split(":")[0] if ":" in usb_bus_id else usb_bus_id
    
    if base_port in BANNED_PORTS:
        if current_time - BANNED_PORTS[base_port] < BAN_TIMEOUT:
            return  
        else:
            del BANNED_PORTS[base_port]

    whitelist = get_whitelist()
    
    if serial == "No Serial" or serial not in whitelist:
        log_event(f"[SENSITIVE] АКТИВНАЯ ЗАЩИТА KIPS: Недоверенное устройство! Блокировка порта {usb_bus_id}...")
        BANNED_PORTS[base_port] = current_time
        
        cmd = f"echo '{usb_bus_id}' > /sys/bus/usb/drivers/usb/unbind"
        try:
            os.system(cmd)
            log_event(f"[SUCCESS] Порт {usb_bus_id} успешно изолирован.")
        except Exception as e:
            log_event(f"[ERROR] Не удалось отключить порт {usb_bus_id}: {e}")
            
        if ":" in usb_bus_id:
            parent_hub = usb_bus_id.split(":")[0]
            log_event(f"[SYSTEM] KIPS: Глубокая изоляция. Отключение родительского хаба {parent_hub}...")
            parent_cmd = f"echo '{parent_hub}' > /sys/bus/usb/drivers/usb/unbind"
            try:
                os.system(parent_cmd)
                log_event(f"[SUCCESS] Родительский хаб {parent_hub} полностью заблокирован.")
            except Exception as e:
                pass
    else:
        log_event(f"[INFO] Устройство {serial} верифицировано в белом списке. Доступ разрешен.")

def monitor_usb():
    log_event("KIPS v1.3: Мониторинг ядерных событий запущен.")
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
                base_port = bus_id.split(":")[0] if bus_id and ":" in bus_id else bus_id
                if base_port not in BANNED_PORTS or (time.time() - BANNED_PORTS.get(base_port, 0) > BAN_TIMEOUT):
                    msg = f"[ALERT] {action} -> {vendor} {model} | S/N: {serial} | Порт: {bus_id}"
                    log_event(msg)
                    if bus_id:
                        disconnect_usb(bus_id, serial)
                else:
                    if bus_id:
                        os.system(f"echo '{bus_id}' > /sys/bus/usb/drivers/usb/unbind 2>/dev/null")
            elif action == "ОТКЛЮЧЕНИЕ":
                base_port = bus_id.split(":")[0] if bus_id and ":" in bus_id else bus_id
                if base_port not in BANNED_PORTS:
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
