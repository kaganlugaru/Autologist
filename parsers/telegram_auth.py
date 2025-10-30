"""
Скрипт для авторизации в Telegram
Запускаем его отдельно для получения нового кода
"""

import asyncio
import os
from telethon import TelegramClient
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def auth_telegram():
    """Авторизация в Telegram"""
    
    # Данные из .env файла
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_name = os.getenv('TELEGRAM_SESSION_NAME', 'autologist_session')
    
    print(f"🔐 Авторизация в Telegram...")
    print(f"📱 API ID: {api_id}")
    print(f"📝 Session: {session_name}")
    
    # Создаем клиент
    client = TelegramClient(session_name, int(api_id), api_hash)
    
    try:
        print(f"🚀 Подключаемся к Telegram...")
        await client.start()
        
        # Проверяем авторизацию
        me = await client.get_me()
        print(f"✅ Успешно авторизован как: {me.first_name} ({me.phone})")
        
        # Получаем список диалогов для проверки
        dialogs = await client.get_dialogs(limit=5)
        print(f"📋 Найдено диалогов: {len(dialogs)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка авторизации: {e}")
        return False
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    print("=" * 50)
    print("🚛 Autologist - Авторизация Telegram")
    print("=" * 50)
    
    success = asyncio.run(auth_telegram())
    
    if success:
        print("✅ Авторизация завершена успешно!")
        print("🚀 Теперь можно запускать парсер")
    else:
        print("❌ Авторизация не удалась")
        print("📋 Проверьте API ключи и попробуйте снова")