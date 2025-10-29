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
        
        # Список чатов для мониторинга (можно настроить в .env)
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
                # Пробуем разные пути к файлу конфигурации
                config_paths = [
                    'config/firebase-service-account.json',
                    'firebase-service-account.json',
                    os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', '')
                ]
                
                config_path = None
                for path in config_paths:
                    if path and os.path.exists(path):
                        config_path = path
                        break
                
                if config_path:
                    cred = credentials.Certificate(config_path)
                    firebase_admin.initialize_app(cred)
                    logger.info("✅ Firebase инициализирован с Service Account")
                else:
                    # Используем конфигурацию из переменных окружения
                    project_id = os.getenv('FIREBASE_PROJECT_ID', 'autologist-91ecf')
                    firebase_admin.initialize_app(options={'projectId': project_id})
                    logger.info("✅ Firebase инициализирован с Project ID")
            
            self.db = firestore.client()
            logger.info("✅ Firestore клиент готов")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Firebase: {e}")
            raise
    
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
                        "keywords": ["груз", "перевозка", "доставка", "транспорт"],
                        "enabled": False
                    }
                ]
                os.makedirs('config', exist_ok=True)
                with open('config/monitored_chats.json', 'w', encoding='utf-8') as f:
                    json.dump(example_chats, f, ensure_ascii=False, indent=2)
                logger.info("📝 Создан пример файла config/monitored_chats.json")
                return []
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки списка чатов: {e}")
            return []
        
    async def start(self):
        """Запуск парсера"""
        logger.info("Запуск Telegram парсера...")
        
        try:
            await self.client.start()
            logger.info("Успешное подключение к Telegram")
            
            # Получаем список чатов
            await self.get_chat_list()
            
            # Запускаем мониторинг новых сообщений
            await self.monitor_messages()
            
        except Exception as e:
            logger.error(f"Ошибка при запуске парсера: {e}")
            
    async def get_chat_list(self):
        """Получение списка доступных чатов"""
        logger.info("Получение списка чатов...")
        
        async for dialog in self.client.iter_dialogs():
            if dialog.is_group:
                chat_info = {
                    'id': dialog.id,
                    'title': dialog.title,
                    'participants': getattr(dialog.entity, 'participants_count', 0)
                }
                logger.info(f"Найден чат: {chat_info['title']} (ID: {chat_info['id']})")
                
    async def monitor_messages(self):
        """Мониторинг новых сообщений"""
        logger.info("Начинаем мониторинг сообщений...")
        
        @self.client.on(events.NewMessage())
        async def handler(event):
            await self.process_message(event)
            
        # Запуск бесконечного цикла
        await self.client.run_until_disconnected()
        
    async def process_message(self, event):
        """Обработка нового сообщения"""
        try:
            message = event.message
            
            # Пропускаем сообщения не из групп
            if not hasattr(event.chat, 'title'):
                return
                
            # Создаем хеш для дедупликации
            message_hash = self.create_message_hash(
                message.text or "", 
                str(message.sender_id)
            )
            
            # Проверяем на дубликаты
            if await self.is_duplicate(message_hash):
                logger.debug(f"Найден дубликат сообщения: {message_hash}")
                return
                
            # Сохраняем в Firebase
            await self.save_message(message, event.chat, message_hash)
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            
    def create_message_hash(self, text, sender_id):
        """Создание хеша сообщения для дедупликации"""
        # Убираем числа из текста (цены могут отличаться)
        clean_text = ''.join(char for char in text if not char.isdigit())
        
        # Создаем хеш
        hash_string = f"{clean_text}_{sender_id}"
        return hashlib.md5(hash_string.encode()).hexdigest()
        
    async def is_duplicate(self, message_hash):
        """Проверка на дубликат сообщения"""
        try:
            # Ищем сообщения с таким же хешем за последние 24 часа
            yesterday = datetime.now() - timedelta(hours=24)
            
            docs = self.db.collection('raw_messages') \
                .where('hash', '==', message_hash) \
                .where('timestamp', '>=', yesterday) \
                .limit(1) \
                .get()
                
            return len(docs) > 0
            
        except Exception as e:
            logger.error(f"Ошибка проверки дубликата: {e}")
            return False
            
    async def save_message(self, message, chat, message_hash):
        """Сохранение сообщения в Firebase"""
        try:
            doc_data = {
                'text': message.text or "",
                'timestamp': datetime.now(),
                'chat_id': chat.id,
                'chat_title': getattr(chat, 'title', 'Unknown'),
                'sender_id': message.sender_id,
                'message_id': message.id,
                'hash': message_hash,
                'processed': False,
                'has_media': message.media is not None
            }
            
            # Сохраняем в коллекцию raw_messages
            doc_ref = self.db.collection('raw_messages').add(doc_data)
            
            logger.info(f"Сохранено сообщение из {chat.title}: {message.text[:50]}...")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения сообщения: {e}")

    async def get_chat_history(self, chat_id, limit=100):
        """Получение истории сообщений из чата"""
        logger.info(f"Получение истории чата {chat_id} (лимит: {limit})")
        
        try:
            async for message in self.client.iter_messages(chat_id, limit=limit):
                await self.process_message_from_history(message, chat_id)
                
        except Exception as e:
            logger.error(f"Ошибка получения истории: {e}")

async def main():
    """Основная функция"""
    parser = TelegramParser()
    await parser.start()

if __name__ == "__main__":
    # Создаем папку для логов если её нет
    os.makedirs('logs', exist_ok=True)
    
    # Запускаем парсер
    asyncio.run(main())