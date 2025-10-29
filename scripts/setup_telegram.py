"""
Скрипт для настройки и тестирования Telegram парсера
Помогает получить API ключи и протестировать подключение
"""

import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

async def setup_telegram():
    """Настройка Telegram API"""
    print("🔧 Настройка Telegram парсера")
    print("=" * 40)
    
    # Проверяем наличие API данных
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    if not api_id or not api_hash:
        print("❌ API данные не найдены в .env файле")
        print("\n📋 Инструкции по получению API:")
        print("1. Перейдите на https://my.telegram.org")
        print("2. Войдите с помощью номера телефона")
        print("3. Перейдите в 'API development tools'")
        print("4. Создайте новое приложение:")
        print("   - App title: Autologist Parser")
        print("   - Short name: autologist")
        print("   - Platform: Desktop")
        print("   - Description: Cargo transportation automation")
        print("5. Скопируйте api_id и api_hash")
        print("6. Создайте файл .env и добавьте:")
        print("   TELEGRAM_API_ID=ваш_api_id")
        print("   TELEGRAM_API_HASH=ваш_api_hash")
        return False
    
    print(f"✅ API ID найден: {api_id}")
    print("✅ API Hash найден")
    
    # Тестируем подключение
    try:
        client = TelegramClient('test_session', int(api_id), api_hash)
        
        print("\n🔌 Тестируем подключение к Telegram...")
        await client.start()
        
        me = await client.get_me()
        print(f"✅ Успешное подключение!")
        print(f"👤 Пользователь: {me.first_name} (@{me.username})")
        print(f"📞 Телефон: {me.phone}")
        
        # Получаем список групп и каналов
        print("\n📋 Ваши группы и каналы:")
        groups_count = 0
        cargo_groups = []
        
        async for dialog in client.iter_dialogs(limit=50):
            if dialog.is_group or dialog.is_channel:
                groups_count += 1
                title_lower = dialog.title.lower()
                
                # Ищем группы связанные с грузоперевозками
                cargo_keywords = ['груз', 'перевозка', 'доставка', 'транспорт', 'логистика', 'фура']
                is_cargo = any(keyword in title_lower for keyword in cargo_keywords)
                
                if is_cargo:
                    cargo_groups.append({
                        'title': dialog.title,
                        'id': dialog.id,
                        'type': 'канал' if dialog.is_channel else 'группа'
                    })
                
                status = "🚛" if is_cargo else "💬"
                group_type = "канал" if dialog.is_channel else "группа"
                print(f"{status} {dialog.title} ({group_type}) - ID: {dialog.id}")
        
        print(f"\n📊 Статистика:")
        print(f"   Всего групп/каналов: {groups_count}")
        print(f"   Связанных с грузоперевозками: {len(cargo_groups)}")
        
        if cargo_groups:
            print(f"\n🚛 Рекомендуемые для мониторинга:")
            for group in cargo_groups:
                print(f"   • {group['title']} ({group['type']}) - ID: {group['id']}")
        
        await client.disconnect()
        
        # Удаляем тестовую сессию
        if os.path.exists('test_session.session'):
            os.remove('test_session.session')
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

async def main():
    """Основная функция"""
    print("🚛 Autologist Telegram Parser Setup")
    print("=" * 40)
    
    success = await setup_telegram()
    
    if success:
        print("\n✅ Настройка завершена успешно!")
        print("\n🚀 Для запуска парсера используйте:")
        print("   python parsers/telegram_parser_v2.py")
        print("\n📝 Для настройки мониторинга отредактируйте:")
        print("   config/monitored_chats.json")
    else:
        print("\n❌ Настройка не завершена")
        print("📖 Следуйте инструкциям выше для получения API ключей")

if __name__ == "__main__":
    asyncio.run(main())