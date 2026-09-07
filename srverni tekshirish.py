#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cleanup_bot.py
==============
Server diski to'lib qolganda avtomatik ishga tushadigan, lekin har bir
o'chirish amalidan oldin Telegram orqali sizdan ruxsat so'raydigan bot.

ISHLASH MANTIG'I
-----------------
1. Har CHECK_INTERVAL_SEC soniyada disk foizini tekshiradi.
2. Agar THRESHOLD_PERCENT dan oshsa, CLEANUP_TARGETS ro'yxatidagi har bir
   manbaning egallagan hajmini hisoblaydi.
3. Telegramga: "Disk 91% to'lgan. <Nomi> ni tozalasammi? (hajmi: 2.3 GB)"
   degan xabarni "Ha" / "Yo'q" tugmalari bilan yuboradi.
4. Sizning javobingizni kutadi (APPROVAL_TIMEOUT_SEC gacha).
5. "Ha" desangiz — o'sha manbani o'chiradi/tozalaydi va natijani yozadi.
   "Yo'q" desangiz yoki javob kelmasa — tegmaydi, keyingisiga o'tadi.

O'RNATISH
---------
    pip install requests --break-system-packages

    # Bot tokenini @BotFather dan oling, chat_id ni esa
    # https://api.telegram.org/bot<TOKEN>/getUpdates orqali botga
    # /start yozib, javobdagi "chat":{"id":...} dan bilib oling.

    export TG_BOT_TOKEN="123456:AAAA...."
    export TG_CHAT_ID="123456789"

ISHGA TUSHIRISH
----------------
    # Doimiy ishlab turadigan rejim (fon jarayoni sifatida, masalan systemd bilan):
    python3 cleanup_bot.py

    # Threshold kutmasdan, darhol tekshirib ko'rish (TEST uchun):
    python3 cleanup_bot.py --test

    # Hech narsani o'chirmasdan, faqat nima topilganini ko'rish:
    python3 cleanup_bot.py --test --dry-run
"""

import os
import sys
import time
import shutil
import logging
import argparse
import subprocess
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests kutubxonasi yo'q. O'rnating: pip install requests --break-system-packages")

# ============================ SOZLAMALAR ============================

BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TG_CHAT_ID", "")

DISK_PATH = "/"                 # qaysi diskni kuzatish
THRESHOLD_PERCENT = 85          # shu foizdan oshsa ishga tushadi
CHECK_INTERVAL_SEC = 300        # necha soniyada bir marta tekshiradi (5 daqiqa)
APPROVAL_TIMEOUT_SEC = 600      # javobni necha soniya kutadi (10 daqiqa)
POLL_INTERVAL_SEC = 2           # Telegramdan javobni qancha tez-tez so'raydi

LOG_FILE = "/var/log/cleanup_bot.log"

# Tozalash mumkin bo'lgan manbalar. Kerak bo'lsa qo'shib/o'chirib turing.
# type="dir_contents" -> papka ichidagi hamma narsani o'chiradi
# type="old_files"    -> papka ichidan faqat min_age_days dan eski fayllarni o'chiradi
# type="cmd"          -> berilgan komandani ishga tushiradi (masalan journalctl, docker)
CLEANUP_TARGETS = [
    {
        "name": "APT paket keshi (/var/cache/apt/archives)",
        "type": "dir_contents",
        "path": "/var/cache/apt/archives",
    },
    {
        "name": "Foydalanuvchi keshi (~/.cache)",
        "type": "dir_contents",
        "path": str(Path.home() / ".cache"),
    },
    {
        "name": "/tmp dagi 3 kundan eski fayllar",
        "type": "old_files",
        "path": "/tmp",
        "min_age_days": 3,
    },
    {
        "name": "/var/log dagi 30 kundan eski log fayllar",
        "type": "old_files",
        "path": "/var/log",
        "min_age_days": 30,
        "pattern": "*.log*",
    },
    {
        "name": "Systemd journal loglari (7 kundan eski qismi)",
        "type": "cmd",
        "size_cmd": ["journalctl", "--disk-usage"],
        "cmd": ["journalctl", "--vacuum-time=7d"],
    },
    {
        "name": "Pip keshi",
        "type": "cmd",
        "size_path": str(Path.home() / ".cache" / "pip"),
        "cmd": ["pip", "cache", "purge"],
    },
    {
        "name": "Docker keraksiz obyektlar (to'xtagan konteyner/image/volume)",
        "type": "cmd",
        "size_cmd": ["docker", "system", "df"],
        "cmd": ["docker", "system", "prune", "-af"],
    },
]

# ============================ LOGGING ============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        # Agar /var/log ga yozish huquqi bo'lmasa, quyidagi qatorni o'chirib qo'ying
        # yoki LOG_FILE ni o'zingiz yoza oladigan joyga o'zgartiring.
    ],
)
try:
    logging.getLogger().addHandler(logging.FileHandler(LOG_FILE))
except Exception:
    logging.warning("Log faylga yoza olmadim (%s), faqat konsolga yozaman.", LOG_FILE)

log = logging.getLogger(__name__)


# ============================ YORDAMCHI FUNKSIYALAR ============================

def human_size(num_bytes: float) -> str:
    """Baytlarni odam o'qiy oladigan formatga o'giradi (KB, MB, GB)."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def get_disk_percent(path: str) -> float:
    total, used, free = shutil.disk_usage(path)
    return used / total * 100


def get_dir_size(path: str) -> int:
    """Papka ichidagi hamma faylning umumiy hajmini hisoblaydi."""
    total = 0
    p = Path(path)
    if not p.exists():
        return 0
    for f in p.rglob("*"):
        try:
            if f.is_file():
                total += f.stat().st_size
        except (OSError, PermissionError):
            continue
    return total


def get_old_files_size(path: str, min_age_days: int, pattern: str = "*") -> int:
    """Berilgan yoshdan eski fayllarning umumiy hajmini hisoblaydi."""
    total = 0
    cutoff = time.time() - min_age_days * 86400
    p = Path(path)
    if not p.exists():
        return 0
    for f in p.rglob(pattern):
        try:
            if f.is_file() and f.stat().st_mtime < cutoff:
                total += f.stat().st_size
        except (OSError, PermissionError):
            continue
    return total


def estimate_target_size(target: dict) -> int:
    """Har bir CLEANUP_TARGETS elementi uchun taxminiy tozalanadigan hajmni hisoblaydi."""
    t = target["type"]
    if t == "dir_contents":
        return get_dir_size(target["path"])
    if t == "old_files":
        return get_old_files_size(target["path"], target["min_age_days"], target.get("pattern", "*"))
    if t == "cmd":
        if "size_path" in target:
            return get_dir_size(target["size_path"])
        # size_cmd bo'lsa - bu faqat ma'lumot uchun, aniq son bermaydi
        return -1  # noma'lum hajm belgisi
    return 0


def delete_target(target: dict) -> str:
    """Tasdiqlangandan keyin haqiqiy tozalashni bajaradi. Natija matnini qaytaradi."""
    t = target["type"]
    try:
        if t == "dir_contents":
            p = Path(target["path"])
            if not p.exists():
                return "Papka topilmadi, o'tkazib yuborildi."
            removed = 0
            for item in p.iterdir():
                try:
                    if item.is_file() or item.is_symlink():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                    removed += 1
                except (OSError, PermissionError) as e:
                    log.warning("O'chira olmadim %s: %s", item, e)
            return f"{removed} ta element o'chirildi."

        if t == "old_files":
            p = Path(target["path"])
            cutoff = time.time() - target["min_age_days"] * 86400
            removed = 0
            for f in p.rglob(target.get("pattern", "*")):
                try:
                    if f.is_file() and f.stat().st_mtime < cutoff:
                        f.unlink()
                        removed += 1
                except (OSError, PermissionError) as e:
                    log.warning("O'chira olmadim %s: %s", f, e)
            return f"{removed} ta eski fayl o'chirildi."

        if t == "cmd":
            result = subprocess.run(
                target["cmd"], capture_output=True, text=True, timeout=300
            )
            output = (result.stdout or result.stderr or "").strip()
            return f"Komanda bajarildi. Natija: {output[:300]}"

    except Exception as e:
        log.exception("Tozalashda xatolik: %s", target.get("name"))
        return f"Xatolik yuz berdi: {e}"

    return "Noma'lum turdagi manba."


# ============================ TELEGRAM ============================

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def tg_send_message(text: str, reply_markup: dict | None = None) -> int | None:
    """Xabar yuboradi va Telegram message_id sini qaytaradi."""
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()["result"]["message_id"]
    except Exception as e:
        log.error("Telegramga xabar yubora olmadim: %s", e)
        return None


def tg_answer_callback(callback_query_id: str, text: str = ""):
    try:
        requests.post(
            f"{API_URL}/answerCallbackQuery",
            json={"callback_query_id": callback_query_id, "text": text},
            timeout=10,
        )
    except Exception:
        pass


def ask_permission(name: str, size_bytes: int) -> bool:
    """Telegramga Ha/Yo'q tugmali savol yuboradi va javobni kutadi."""
    size_text = human_size(size_bytes) if size_bytes >= 0 else "hajmi noma'lum"
    text = f"⚠️ Disk to'lib bormoqda.\n\n<b>{name}</b>\nTaxminiy hajm: {size_text}\n\nBuni tozalasammi?"
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Ha, tozala", "callback_data": "yes"},
            {"text": "❌ Yo'q, tegma", "callback_data": "no"},
        ]]
    }
    msg_id = tg_send_message(text, reply_markup=keyboard)
    if msg_id is None:
        return False

    log.info("Ruxsat so'raldi: %s (hajm: %s). Javob kutilmoqda...", name, size_text)

    deadline = time.time() + APPROVAL_TIMEOUT_SEC
    offset = None
    while time.time() < deadline:
        try:
            resp = requests.get(
                f"{API_URL}/getUpdates",
                params={"timeout": POLL_INTERVAL_SEC, "offset": offset},
                timeout=POLL_INTERVAL_SEC + 10,
            )
            updates = resp.json().get("result", [])
        except Exception as e:
            log.warning("getUpdates xatosi: %s", e)
            time.sleep(POLL_INTERVAL_SEC)
            continue

        for upd in updates:
            offset = upd["update_id"] + 1
            cq = upd.get("callback_query")
            if not cq:
                continue
            if str(cq["message"]["message_id"]) != str(msg_id):
                continue
            data = cq.get("data")
            tg_answer_callback(cq["id"], "Qabul qilindi." if data == "yes" else "Bekor qilindi.")
            return data == "yes"

    tg_send_message(f"⏱ '{name}' uchun javob kelmadi ({APPROVAL_TIMEOUT_SEC}s), o'tkazib yuborildi.")
    return False


# ============================ ASOSIY MANTIQ ============================

def run_cleanup_cycle(dry_run: bool = False):
    percent = get_disk_percent(DISK_PATH)
    log.info("Disk holati: %.1f%% ishlatilgan (%s)", percent, DISK_PATH)

    if percent < THRESHOLD_PERCENT and not dry_run:
        return

    tg_send_message(f"📊 Disk {percent:.1f}% to'lgan (limit: {THRESHOLD_PERCENT}%). "
                     f"Tozalash uchun nomzodlarni tekshiryapman...")

    for target in CLEANUP_TARGETS:
        size = estimate_target_size(target)
        size_text = human_size(size) if size >= 0 else "noma'lum"
        log.info("Nomzod: %-55s hajmi: %s", target["name"], size_text)

        if size == 0:
            continue  # o'chiradigan narsa yo'q ekan, so'ramaymiz

        if dry_run:
            log.info("[DRY-RUN] '%s' o'chirilmadi (faqat ko'rsatish rejimi).", target["name"])
            continue

        approved = ask_permission(target["name"], size)
        if approved:
            result = delete_target(target)
            tg_send_message(f"🧹 <b>{target['name']}</b>\n{result}")
            log.info("Tozalandi: %s -> %s", target["name"], result)
        else:
            tg_send_message(f"➡️ <b>{target['name']}</b> o'tkazib yuborildi.")
            log.info("O'tkazib yuborildi: %s", target["name"])

    new_percent = get_disk_percent(DISK_PATH)
    tg_send_message(f"✅ Tsikl tugadi. Yangi disk holati: {new_percent:.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Telegram orqali ruxsat so'rab disk tozalash bot")
    parser.add_argument("--test", action="store_true",
                         help="Threshold ni kutmasdan darhol bir marta tekshiradi (test uchun)")
    parser.add_argument("--dry-run", action="store_true",
                         help="Hech narsani o'chirmaydi, faqat nomzodlar va hajmlarini ko'rsatadi")
    args = parser.parse_args()

    if not BOT_TOKEN or not CHAT_ID:
        sys.exit("TG_BOT_TOKEN va TG_CHAT_ID environment o'zgaruvchilarini o'rnating.")

    if args.test:
        log.info("TEST rejimi: bitta tsikl ishga tushirilmoqda (dry_run=%s)", args.dry_run)
        run_cleanup_cycle(dry_run=args.dry_run)
        return

    log.info("Bot ishga tushdi. Har %ss da disk tekshiriladi, limit: %s%%",
              CHECK_INTERVAL_SEC, THRESHOLD_PERCENT)
    while True:
        try:
            run_cleanup_cycle(dry_run=False)
        except Exception:
            log.exception("Asosiy tsiklda xatolik yuz berdi")
        time.sleep(CHECK_INTERVAL_SEC)


if __name__ == "__main__":
    main()