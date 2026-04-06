import asyncio
import re
import traceback
from pathlib import Path
from datetime import timedelta

from telethon import TelegramClient, events

API_ID = 31467257
API_HASH = "cc4949a16fc012b878db15a9c6f9020f"

BASE_DIR = Path(r"D:\TelegramFiles")
SESSION_NAME = "telegram_media_session"


def sanitize_name(name: str) -> str:
    if not name:
        name = "Unknown"
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:120]


def get_file_category(ext: str) -> str:
    ext = ext.lower()
    if ext == ".pdf":
        return "PDF"
    elif ext in [".xls", ".xlsx", ".csv"]:
        return "Excel"
    elif ext in [".doc", ".docx", ".rtf"]:
        return "Word"
    elif ext in [".zip", ".rar", ".7z"]:
        return "Архивы"
    elif ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]:
        return "Изображения"
    elif ext in [".txt"]:
        return "Текст"
    else:
        return "Другое"


def build_unique_path(target_path: Path) -> Path:
    if not target_path.exists():
        return target_path

    stem = target_path.stem
    suffix = target_path.suffix
    parent = target_path.parent

    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


async def get_chat_folder_name(event) -> str:
    chat = await event.get_chat()

    title = getattr(chat, "title", None)
    if title:
        return sanitize_name(title)

    first_name = getattr(chat, "first_name", "") or ""
    last_name = getattr(chat, "last_name", "") or ""
    username = getattr(chat, "username", "") or ""

    full_name = f"{first_name} {last_name}".strip()
    if full_name:
        return sanitize_name(full_name)

    if username:
        return sanitize_name(username)

    return "PrivateChat"


def get_chat_type(chat) -> str:
    if getattr(chat, "broadcast", False):
        return "Каналы"
    elif getattr(chat, "megagroup", False):
        return "Группы"
    elif getattr(chat, "title", None):
        return "Группы"
    else:
        return "Личные"


def get_media_filename(msg) -> str:
    if msg.file and msg.file.name:
        return sanitize_name(msg.file.name)

    if msg.photo:
        return f"photo_{msg.id}.jpg"

    if msg.video:
        ext = msg.file.ext if msg.file and msg.file.ext else ".mp4"
        return f"video_{msg.id}{ext}"

    if msg.audio:
        ext = msg.file.ext if msg.file and msg.file.ext else ".mp3"
        return f"audio_{msg.id}{ext}"

    if msg.voice:
        ext = msg.file.ext if msg.file and msg.file.ext else ".ogg"
        return f"voice_{msg.id}{ext}"

    ext = msg.file.ext if msg.file and msg.file.ext else ""
    return f"file_{msg.id}{ext}"


async def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(
        SESSION_NAME,
        API_ID,
        API_HASH,
        sequential_updates=True
    )

    await client.start()
    me = await client.get_me()

    print("=" * 70)
    print("Скрипт запущен.")
    print(f"Папка сохранения: {BASE_DIR}")
    print(f"Авторизован как: {getattr(me, 'first_name', '')} {getattr(me, 'last_name', '')}".strip())
    print("Жду новые сообщения с файлами...")
    print("=" * 70)

    @client.on(events.NewMessage)
    async def handler(event):
        try:
            print("-" * 70)
            print("ПОЙМАНО НОВОЕ СООБЩЕНИЕ")

            msg = event.message
            if not msg:
                print("Нет объекта message")
                return

            if not msg.media:
                print("Это сообщение без медиа, пропускаю")
                return

            print(f"ID сообщения: {msg.id}")
            print(f"Есть media: {bool(msg.media)}")
            print(f"Есть file: {bool(msg.file)}")
            print(f"event.out: {event.out}")

            original_name = get_media_filename(msg)
            ext = Path(original_name).suffix.lower()

            msg_dt_local = msg.date + timedelta(hours=5)
            msg_date = msg_dt_local.strftime("%d.%m.%Y")
            new_name = f"{msg_date}_{original_name}"

            chat = await event.get_chat()
            chat_type = get_chat_type(chat)
            folder_name = await get_chat_folder_name(event)
            file_type = get_file_category(ext)

            target_dir = BASE_DIR / chat_type / folder_name / file_type
            target_dir.mkdir(parents=True, exist_ok=True)

            target_path = build_unique_path(target_dir / new_name)

            print(f"Чат: {chat_type} / {folder_name}")
            print(f"Имя файла: {original_name}")
            print(f"Дата сообщения: {msg_dt_local.strftime('%d.%m.%Y %H:%M:%S')}")
            print(f"Сохраняю в: {target_path}")

            saved_path = await msg.download_media(file=str(target_path))

            if saved_path:
                print(f"ГОТОВО: {saved_path}")
            else:
                print("download_media вернул пустой путь")

        except Exception:
            print("!!! ОШИБКА ПРИ ОБРАБОТКЕ !!!")
            traceback.print_exc()

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())