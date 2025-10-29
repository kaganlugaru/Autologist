"""
Telegram парсер для сбора сообщений из групповых чатов
Использует Telethon для подключения к Telegram API
"""

import asyncio
import os
import hashlib
from datetime import datetime, timedelta
from telethon import TelegramClient
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import logging

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_parser.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramParser:
    def __init__(self):
        """Инициализация парсера"""
        # Telegram API данные
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.session_name = os.getenv('TELEGRAM_SESSION_NAME', 'autologist_session')
        
        # Инициализация Telegram клиента
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        # Инициализация Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate('config/firebase-service-account.json')
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        
        # Список ID чатов для мониторинга (заполнить позже)
        self.monitored_chats = []
        
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