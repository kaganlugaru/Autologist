"""
Скрипт для инициализации структуры базы данных Firestore
Создает коллекции и добавляет тестовые данные
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import os

def initialize_firestore():
    """Инициализация Firestore и создание начальной структуры"""
    
    # Инициализация Firebase Admin (используем Application Default Credentials)
    try:
        # Попробуем инициализировать с настройками проекта
        if not firebase_admin._apps:
            # Используем переменные окружения для конфигурации
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': 'autologist-65cd7'
            })
        
        db = firestore.client()
        print("✅ Подключение к Firestore успешно!")
        
        # Создаем тестовые данные для демонстрации
        create_sample_data(db)
        
    except Exception as e:
        print(f"❌ Ошибка инициализации Firebase: {e}")
        print("\n💡 Для работы скрипта нужно:")
        print("1. Установить Firebase CLI: npm install -g firebase-tools")
        print("2. Войти в аккаунт: firebase login")
        print("3. Установить проект: firebase use autologist-65cd7")
        return False
    
    return True

def create_sample_data(db):
    """Создание тестовых данных"""
    
    print("📝 Создаем тестовые данные...")
    
    # 1. Тестовые сырые сообщения
    raw_messages = [
        {
            'text': 'Везу мебель Москва-Питер, 5 тонн, 40000 руб, тел 89991234567',
            'timestamp': datetime.now(),
            'chat_id': -1001234567890,
            'chat_title': 'Грузы Москва-СПб',
            'sender_id': 123456789,
            'message_id': 1001,
            'hash': 'sample_hash_1',
            'processed': False,
            'has_media': False
        },
        {
            'text': 'Нужен транспорт: Новосибирск → Екатеринбург, продукты, 3т, срочно!',
            'timestamp': datetime.now() - timedelta(hours=2),
            'chat_id': -1001234567891,
            'chat_title': 'Сибирские грузы',
            'sender_id': 987654321,
            'message_id': 1002,
            'hash': 'sample_hash_2',
            'processed': True,
            'has_media': False
        },
        {
            'text': 'Стройматериалы Казань-Самара, 8 тонн, тент, 60к',
            'timestamp': datetime.now() - timedelta(hours=5),
            'chat_id': -1001234567892,
            'chat_title': 'Поволжье логистика',
            'sender_id': 555666777,
            'message_id': 1003,
            'hash': 'sample_hash_3',
            'processed': True,
            'has_media': False
        }
    ]
    
    # Добавляем сырые сообщения
    for i, message in enumerate(raw_messages):
        doc_ref = db.collection('raw_messages').add(message)
        print(f"✅ Добавлено сырое сообщение {i+1}")
    
    # 2. Тестовые обработанные грузы
    processed_cargos = [
        {
            'from_city': 'Москва',
            'to_city': 'Санкт-Петербург',
            'cargo_type': 'мебель',
            'weight': '5 тонн',
            'volume': 'не указан',
            'price': '40000 руб',
            'contact': '89991234567',
            'urgency': 'обычная',
            'timestamp': datetime.now(),
            'original_message_id': 'sample_hash_1',
            'status': 'новый'
        },
        {
            'from_city': 'Новосибирск',
            'to_city': 'Екатеринбург', 
            'cargo_type': 'продукты',
            'weight': '3 тонны',
            'volume': 'не указан',
            'price': 'договорная',
            'contact': 'не указан',
            'urgency': 'высокая',
            'timestamp': datetime.now() - timedelta(hours=2),
            'original_message_id': 'sample_hash_2',
            'status': 'в работе'
        },
        {
            'from_city': 'Казань',
            'to_city': 'Самара',
            'cargo_type': 'стройматериалы',
            'weight': '8 тонн',
            'volume': 'тент',
            'price': '60000 руб',
            'contact': 'не указан',
            'urgency': 'обычная',
            'timestamp': datetime.now() - timedelta(hours=5),
            'original_message_id': 'sample_hash_3',
            'status': 'новый'
        }
    ]
    
    # Добавляем обработанные грузы
    for i, cargo in enumerate(processed_cargos):
        doc_ref = db.collection('processed_cargos').add(cargo)
        print(f"✅ Добавлен обработанный груз {i+1}")
    
    # 3. Статистика
    stats_data = {
        'total_messages': len(raw_messages),
        'processed_cargos': len(processed_cargos),
        'active_chats': 3,
        'last_update': datetime.now(),
        'daily_stats': {
            'today_messages': 1,
            'today_processed': 1
        }
    }
    
    db.collection('statistics').document('current').set(stats_data)
    print("✅ Добавлена статистика")
    
    print("\n🎉 Инициализация завершена!")
    print(f"📊 Создано:")
    print(f"   - {len(raw_messages)} сырых сообщений")
    print(f"   - {len(processed_cargos)} обработанных грузов")
    print(f"   - 1 запись статистики")

if __name__ == "__main__":
    print("🔥 Инициализация базы данных Firestore...")
    print("🎯 Проект: autologist-65cd7")
    print("-" * 50)
    
    if initialize_firestore():
        print("\n✅ Инициализация успешно завершена!")
        print("🌐 Обновите веб-интерфейс чтобы увидеть данные")
    else:
        print("\n❌ Инициализация не удалась")