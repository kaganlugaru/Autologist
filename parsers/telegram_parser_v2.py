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
    
    import os
    import json
    import time

    def load_monitored_chats(self, force_update=False):
        """
        Загрузка списка отслеживаемых чатов с локальным кэшированием.
        Если force_update=True или кэш устарел/отсутствует — обновляет из Firestore.
        """
        CACHE_PATH = 'config/monitored_chats_cache.json'
        CACHE_TTL = 60 * 60  # 1 час (можно изменить)
        try:
            # Проверяем кэш
            if not force_update and os.path.exists(CACHE_PATH):
                mtime = os.path.getmtime(CACHE_PATH)
                if time.time() - mtime < CACHE_TTL:
                    with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                        chats = json.load(f)
                    logger.info(f"✅ Загружено {len(chats)} чатов из локального кэша")
                    return chats
            # Если кэш устарел или принудительное обновление — грузим из Firestore
            from google.cloud import firestore
            db = firestore.Client()
            chats_ref = db.collection('monitored_chats')
            chats = [doc.to_dict() for doc in chats_ref.stream()]
            # Сохраняем в кэш
            os.makedirs('config', exist_ok=True)
            with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump(chats, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Загружено {len(chats)} чатов для мониторинга из Firestore и обновлён кэш")
            return chats
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки списка чатов: {e}")
            return []

    def force_update_monitored_chats_cache(self):
        """Принудительное обновление локального кэша monitored_chats из Firestore"""
        return self.load_monitored_chats(force_update=True)
    
    def create_message_hash(self, text, sender_id, chat_id):
        """Создание хеша для дедупликации сообщений"""
        hash_string = f"{text}_{sender_id}_{chat_id}"
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def is_cargo_related(self, text, keywords):
        """Проверка содержит ли сообщение ключевые слова о грузах"""
        if not text:
            return False, []
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in keywords:
            kw = keyword.lower().strip()
            if kw and kw in text_lower:
                found_keywords.append(keyword)
        
        return len(found_keywords) > 0, found_keywords
    
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
        """Настройка обработчиков сообщений только для выбранных чатов"""
        # Получаем список chat_id для мониторинга
        monitored_ids = set()
        for chat in self.monitored_chats:
            if chat.get('enabled', True) and chat.get('chat_id'):
                cid = str(chat['chat_id'])
                monitored_ids.add(cid)
                if cid.startswith('-100'):
                    monitored_ids.add(cid[4:])
                if cid.startswith('-'):
                    monitored_ids.add(cid[1:])
        
        @self.client.on(events.NewMessage())
        async def handle_new_message(event):
            chat = await event.get_chat()
            chat_id_str = str(getattr(chat, 'id', ''))
            if chat_id_str not in monitored_ids:
                return
            await self.process_message(event)
        
        logger.info(f"✅ Обработчики сообщений настроены только для чатов: {[c['chat_id'] for c in self.monitored_chats if c.get('enabled', True)]}")
    
    async def process_message(self, event):
        """Обработка нового сообщения"""
        try:
            message = event.message
            chat = await event.get_chat()
            
            # Отладочная информация о всех сообщениях
            logger.info(f"📨 Получено сообщение от чата: {getattr(chat, 'title', 'Без названия')} (ID: {chat.id})")
            
            # Дополнительная отладка для тестового чата
            if hasattr(chat, 'title') and ("тест" in chat.title.lower() or "автологист" in chat.title.lower()):
                logger.info(f"🧪 ТЕСТОВЫЙ ЧАТ: {chat.title}")
                logger.info(f"🧪 ID: {chat.id}")
                logger.info(f"🧪 Тип чата: megagroup={getattr(chat, 'megagroup', None)}, broadcast={getattr(chat, 'broadcast', None)}")
                logger.info(f"🧪 Текст: {message.text[:100] if message.text else 'Нет текста'}...")
            
            # Пропускаем личные сообщения  
            if not (hasattr(chat, 'title') and (getattr(chat, 'megagroup', False) or getattr(chat, 'broadcast', False) or hasattr(chat, 'participants_count'))):
                # Дополнительная проверка для обычных групп
                if not hasattr(chat, 'title'):
                    return  # Точно личное сообщение
                
                # Дополнительная отладка для отклоненных чатов
                logger.debug(f"🚫 Пропускаем чат {getattr(chat, 'title', 'Без названия')}: megagroup={getattr(chat, 'megagroup', None)}, broadcast={getattr(chat, 'broadcast', None)}")
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
            
            # Ищем настройки для данного чата СРАЗУ
            chat_config = None
            chat_id_str = str(chat.id)
            
            # Отладочное логирование для тестового чата
            if "тест автологист" in chat.title.lower():
                logger.info(f"🔍 DEBUG: Ищем настройки для '{chat.title}' с ID: {chat_id_str}")
                config_list = [f"{c.get('title')} ({c.get('chat_id')})" for c in self.monitored_chats]
                logger.info(f"🔍 DEBUG: Доступные чаты в конфигурации: {config_list}")
            
            for monitored_chat in self.monitored_chats:
                config_chat_id = str(monitored_chat.get('chat_id', ''))
                
                # Отладочная информация для тестового чата
                if "тест автологист" in chat.title.lower():
                    logger.info(f"🔍 DEBUG: Сравниваем '{chat_id_str}' с конфигурацией '{config_chat_id}'")
                
                # Сравниваем ID с учетом возможных префиксов -100 и знаков
                if (chat_id_str == config_chat_id or 
                    chat_id_str == config_chat_id.replace('-100', '') or
                    f'-100{chat_id_str}' == config_chat_id or
                    f'-{chat_id_str}' == config_chat_id or
                    chat_id_str == config_chat_id.replace('-', '')):
                    chat_config = monitored_chat
                    logger.info(f"🎯 Найдены настройки для чата {chat.title}: {config_chat_id}")
                    break
            
            # ПРОПУСКАЕМ чаты, которые НЕ в списке мониторинга
            if not chat_config or not chat_config.get('enabled', True):
                logger.debug(f"⏭️ Пропускаем чат {chat.title} - не в списке мониторинга или отключен")
                return
            # Используем ключевые слова из настроек чата (чат уже проверен выше)
            keywords_to_check = chat_config.get('keywords', [])
            logger.info(f"🔑 Используем ключевые слова чата {chat.title}: {keywords_to_check}")
            
            # Подробное логирование для чата Калжат
            if "калжат" in chat.title.lower():
                logger.info(f"🔎 [Калжат] Текст сообщения: {message.text}")
            is_cargo, found_keywords = self.is_cargo_related(message.text, keywords_to_check)
            if "калжат" in chat.title.lower():
                logger.info(f"🔎 [Калжат] Ключевые слова найдены: {found_keywords}")
            if is_cargo:
                await self.save_message(message, chat, message_hash, found_keywords)
                logger.info(f"💾 Сохранено сообщение из {chat.title} по ключевым словам: {', '.join(found_keywords)}")
            else:
                logger.debug(f"❌ Сообщение из {chat.title} не содержит ключевых слов: {message.text[:50]}...")
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Ошибка обработки сообщения: {e}")
    
    async def save_message(self, message, chat, message_hash, found_keywords=None):
        """Сохранение сообщения в Firebase или локально"""
        try:
            # Получаем информацию об отправителе
            sender = await message.get_sender()
            sender_name = ""
            sender_username = ""
            
            if sender:
                # Получаем username (ник с @)
                if hasattr(sender, 'username') and sender.username:
                    sender_username = sender.username
                
                # Получаем имя пользователя
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
                'sender_username': sender_username,
                'timestamp': message.date.isoformat() if message.date else datetime.now().isoformat(),
                'processed': False,
                'hash': message_hash,
                'created_at': datetime.now().isoformat(),
                'keywords_found': found_keywords or []
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