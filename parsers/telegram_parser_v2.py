"""
Telegram парсер для сбора сообщений из групповых чатов
Использует Telethon для подключения к Telegram API
Версия 2.0 - улучшенная обработка и мониторинг
"""

import asyncio
import os
import hashlib
import json
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import logging
import time

# Загружаем переменные окружения
load_dotenv()

# Создаем папку для логов если её нет
os.makedirs('logs', exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_parser.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramParser:
    def __init__(self):
        """Инициализация парсера"""
        logger.info("🚀 Инициализация Telegram парсера...")
        
        # Telegram API данные
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.session_name = os.getenv('TELEGRAM_SESSION_NAME', 'autologist_session')
        
        if not self.api_id or not self.api_hash:
            logger.error("❌ TELEGRAM_API_ID и TELEGRAM_API_HASH должны быть установлены в .env файле")
            raise ValueError("Отсутствуют API данные Telegram")
        
        # Инициализация Telegram клиента
        self.client = TelegramClient(self.session_name, int(self.api_id), self.api_hash)
        
        # Инициализация Firebase
        self.init_firebase()
        
        # Список чатов для мониторинга
        self.monitored_chats = self.load_monitored_chats()
        
        # Кэш для предотвращения дубликатов
        self.processed_messages = set()
        
        # Статистика
        self.stats = {
            'messages_processed': 0,
            'messages_saved': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    def init_firebase(self):
        """Инициализация Firebase"""
        try:
            if not firebase_admin._apps:
                # Используем упрощенную инициализацию для работы с публичными данными
                project_id = os.getenv('FIREBASE_PROJECT_ID', 'autologist-91ecf')
                
                # Пробуем инициализировать без credentials для чтения публичных данных
                try:
                    firebase_admin.initialize_app(options={'projectId': project_id})
                    logger.info("✅ Firebase инициализирован с Project ID")
                except Exception:
                    # Если не получается, создаем временную конфигурацию
                    logger.warning("⚠️  Firebase credentials не найдены, используем временное решение")
                    # Будем сохранять данные локально в JSON файлы
                    self.use_local_storage = True
                    return
            
            self.db = firestore.client()
            self.use_local_storage = False
            logger.info("✅ Firestore клиент готов")
            
        except Exception as e:
            logger.warning(f"⚠️  Firebase недоступен: {e}")
            logger.info("📁 Используем локальное хранение данных")
            self.use_local_storage = True
            # Создаем папки для локального хранения
            os.makedirs('data/messages', exist_ok=True)
    
    def load_monitored_chats(self):
        """Загрузка списка отслеживаемых чатов"""
        try:
            # Пробуем загрузить из файла конфигурации
            if os.path.exists('config/monitored_chats.json'):
                with open('config/monitored_chats.json', 'r', encoding='utf-8') as f:
                    chats = json.load(f)
                logger.info(f"✅ Загружено {len(chats)} чатов для мониторинга")
                return chats
            else:
                # Создаем пример файла конфигурации
                example_chats = [
                    {
                        "name": "Пример канала грузоперевозок",
                        "username": "@cargo_channel_example", 
                        "chat_id": None,
                        "keywords": ["груз", "перевозка", "доставка", "транспорт", "тонн", "маршрут"],
                        "enabled": False
                    }
                ]
                os.makedirs('config', exist_ok=True)
                with open('config/monitored_chats.json', 'w', encoding='utf-8') as f:
                    json.dump(example_chats, f, ensure_ascii=False, indent=2)
                logger.info("📝 Создан пример файла config/monitored_chats.json")
                return example_chats
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки списка чатов: {e}")
            return []
    
    def create_message_hash(self, text, sender_id, chat_id):
        """Создание хеша для дедупликации сообщений"""
        hash_string = f"{text}_{sender_id}_{chat_id}"
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def is_cargo_related(self, text, keywords):
        """Проверка содержит ли сообщение ключевые слова о грузах"""
        if not text:
            return False
            
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    async def start(self):
        """Запуск парсера"""
        logger.info("🚀 Запуск Telegram парсера...")
        
        try:
            # Подключение к Telegram
            await self.client.start()
            
            # Проверяем авторизацию
            me = await self.client.get_me()
            logger.info(f"✅ Подключен как: {me.first_name} (@{me.username})")
            
            # Получаем список доступных чатов
            await self.discover_chats()
            
            # Настраиваем обработчик новых сообщений
            self.setup_message_handlers()
            
            # Запускаем мониторинг
            logger.info("👁️  Начинаем мониторинг сообщений...")
            await self.client.run_until_disconnected()
            
        except SessionPasswordNeededError:
            logger.error("❌ Требуется двухфакторная аутентификация. Запустите парсер в интерактивном режиме.")
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске: {e}")
            raise
    
    async def discover_chats(self):
        """Получение списка доступных чатов и каналов"""
        logger.info("🔍 Ищем доступные чаты и каналы...")
        
        cargo_keywords = ['груз', 'перевозка', 'доставка', 'транспорт', 'логистика', 'фура', 'тонн']
        found_chats = []
        
        async for dialog in self.client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                title_lower = dialog.title.lower()
                is_cargo_chat = any(keyword in title_lower for keyword in cargo_keywords)
                
                chat_info = {
                    'id': dialog.id,
                    'title': dialog.title,
                    'type': 'канал' if dialog.is_channel else 'группа',
                    'participants': getattr(dialog.entity, 'participants_count', 'неизвестно'),
                    'cargo_related': is_cargo_chat
                }
                
                found_chats.append(chat_info)
                
                status = "🚛" if is_cargo_chat else "💬"
                logger.info(f"{status} {chat_info['type']}: {chat_info['title']} (ID: {chat_info['id']}, участников: {chat_info['participants']})")
        
        # Сохраняем найденные чаты
        os.makedirs('config', exist_ok=True)
        with open('config/discovered_chats.json', 'w', encoding='utf-8') as f:
            json.dump(found_chats, f, ensure_ascii=False, indent=2)
        
        cargo_chats = [chat for chat in found_chats if chat['cargo_related']]
        logger.info(f"📊 Найдено {len(found_chats)} чатов, из них {len(cargo_chats)} связанных с грузоперевозками")
    
    def setup_message_handlers(self):
        """Настройка обработчиков сообщений"""
        
        @self.client.on(events.NewMessage())
        async def handle_new_message(event):
            await self.process_message(event)
        
        logger.info("✅ Обработчики сообщений настроены")
    
    async def process_message(self, event):
        """Обработка нового сообщения"""
        try:
            message = event.message
            chat = await event.get_chat()
            
            # Пропускаем личные сообщения
            if not (hasattr(chat, 'title') and (chat.megagroup or chat.broadcast)):
                return
            
            # Пропускаем пустые сообщения
            if not message.text:
                return
            
            self.stats['messages_processed'] += 1
            
            # Создаем хеш для дедупликации
            message_hash = self.create_message_hash(
                message.text, 
                str(message.sender_id), 
                str(chat.id)
            )
            
            # Пропускаем уже обработанные сообщения
            if message_hash in self.processed_messages:
                return
            
            self.processed_messages.add(message_hash)
            
            # Проверяем содержит ли сообщение ключевые слова
            cargo_keywords = ['груз', 'перевозка', 'доставка', 'транспорт', 'тонн', 'маршрут', 'фура', 'газель']
            
            if self.is_cargo_related(message.text, cargo_keywords):
                await self.save_message(message, chat, message_hash)
                logger.info(f"💾 Сохранено сообщение из {chat.title}")
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Ошибка обработки сообщения: {e}")
    
    async def save_message(self, message, chat, message_hash):
        """Сохранение сообщения в Firebase или локально"""
        try:
            # Получаем информацию об отправителе
            sender = await message.get_sender()
            sender_name = ""
            if sender:
                if hasattr(sender, 'first_name') and sender.first_name:
                    sender_name = sender.first_name
                    if hasattr(sender, 'last_name') and sender.last_name:
                        sender_name += f" {sender.last_name}"
                elif hasattr(sender, 'title'):
                    sender_name = sender.title
            
            # Подготавливаем данные для сохранения
            message_data = {
                'text': message.text,
                'source': 'telegram',
                'chat_id': str(chat.id),
                'chat_title': chat.title,
                'message_id': str(message.id),
                'sender_id': str(message.sender_id) if message.sender_id else None,
                'sender_name': sender_name,
                'timestamp': message.date.isoformat() if message.date else datetime.now().isoformat(),
                'processed': False,
                'hash': message_hash,
                'created_at': datetime.now().isoformat()
            }
            
            if hasattr(self, 'use_local_storage') and self.use_local_storage:
                # Сохраняем локально в JSON файл
                filename = f"data/messages/message_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{message_hash[:8]}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(message_data, f, ensure_ascii=False, indent=2)
                logger.info(f"💾 Сообщение сохранено локально: {filename}")
            else:
                # Сохраняем в Firebase
                doc_ref = self.db.collection('messages').add(message_data)
                logger.info(f"✅ Сообщение сохранено в Firebase: {doc_ref[1].id}")
            
            self.stats['messages_saved'] += 1
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Ошибка сохранения сообщения: {e}")
    
    async def get_stats(self):
        """Получение статистики работы"""
        uptime = datetime.now() - self.stats['start_time']
        return {
            **self.stats,
            'uptime': str(uptime),
            'cache_size': len(self.processed_messages)
        }
    
    async def stop(self):
        """Остановка парсера"""
        logger.info("🛑 Остановка парсера...")
        stats = await self.get_stats()
        logger.info(f"📊 Статистика: {stats}")
        await self.client.disconnect()

# Функция для запуска парсера
async def main():
    """Основная функция запуска"""
    parser = TelegramParser()
    
    try:
        await parser.start()
    except KeyboardInterrupt:
        logger.info("⌨️  Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await parser.stop()

if __name__ == "__main__":
    print("🚛 Autologist Telegram Parser v2.0")
    print("=" * 40)
    asyncio.run(main())