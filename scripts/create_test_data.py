"""
Скрипт для создания тестовых данных в Firebase Firestore
Автоматически создает коллекции messages и cargos с тестовыми данными
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import random

def initialize_firebase():
    """Инициализация Firebase Admin SDK"""
    try:
        # Проверяем, инициализирован ли уже Firebase
        firebase_admin.get_app()
        print("✅ Firebase уже инициализирован")
    except ValueError:
        # Инициализируем Firebase с дефолтными настройками
        # Используем Application Default Credentials
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': 'autologist-91ecf'
            })
            print("✅ Firebase инициализирован через Application Default Credentials")
        except Exception as e:
            print("❌ Ошибка инициализации Firebase:", str(e))
            print("\n📝 Для работы скрипта нужно настроить аутентификацию:")
            print("1. Установить Google Cloud CLI")
            print("2. Выполнить: gcloud auth application-default login")
            print("3. Или использовать Service Account Key")
            return None
    
    return firestore.client()

def create_test_messages(db):
    """Создание тестовых сообщений"""
    print("\n📨 Создаем тестовые сообщения...")
    
    test_messages = [
        {
            'text': 'Нужно перевезти груз из Москвы в СПб, 5 тонн, срочно до завтра',
            'source': 'telegram',
            'timestamp': datetime.now(),
            'processed': False,
            'chat_id': 'chat_123',
            'message_id': 'msg_001'
        },
        {
            'text': 'Ищу транспорт для перевозки мебели Екатеринбург -> Челябинск, 2 тонны',
            'source': 'whatsapp',
            'timestamp': datetime.now() - timedelta(hours=2),
            'processed': True,
            'chat_id': 'chat_456',
            'message_id': 'msg_002'
        },
        {
            'text': 'Есть груз 10 тонн металлопроката, Новосибирск - Омск, оплата сразу',
            'source': 'telegram',
            'timestamp': datetime.now() - timedelta(hours=5),
            'processed': False,
            'chat_id': 'chat_789',
            'message_id': 'msg_003'
        },
        {
            'text': 'Нужна газель для перевозки коробок по городу, 500 кг максимум',
            'source': 'whatsapp',
            'timestamp': datetime.now() - timedelta(hours=8),
            'processed': True,
            'chat_id': 'chat_101',
            'message_id': 'msg_004'
        }
    ]
    
    messages_collection = db.collection('messages')
    
    for i, message_data in enumerate(test_messages, 1):
        try:
            doc_ref = messages_collection.add(message_data)
            print(f"✅ Сообщение {i} создано: {doc_ref[1].id}")
        except Exception as e:
            print(f"❌ Ошибка создания сообщения {i}: {str(e)}")

def create_test_cargos(db):
    """Создание тестовых грузов"""
    print("\n📦 Создаем тестовые грузы...")
    
    test_cargos = [
        {
            'from': 'Москва',
            'to': 'Санкт-Петербург',
            'weight': 5.0,
            'price': 45000,
            'status': 'активный',
            'cargoType': 'стройматериалы',
            'timestamp': datetime.now(),
            'contact': '+7 (900) 123-45-67',
            'description': 'Кирпич и цемент для стройки',
            'urgent': True
        },
        {
            'from': 'Екатеринбург',
            'to': 'Челябинск',
            'weight': 2.0,
            'price': 25000,
            'status': 'в пути',
            'cargoType': 'мебель',
            'timestamp': datetime.now() - timedelta(hours=3),
            'contact': '+7 (900) 234-56-78',
            'description': 'Офисная мебель (столы, стулья)',
            'urgent': False
        },
        {
            'from': 'Новосибирск',
            'to': 'Омск',
            'weight': 10.0,
            'price': 80000,
            'status': 'активный',
            'cargoType': 'металлопрокат',
            'timestamp': datetime.now() - timedelta(hours=6),
            'contact': '+7 (900) 345-67-89',
            'description': 'Листовая сталь и профиль',
            'urgent': True
        },
        {
            'from': 'Казань',
            'to': 'Самара',
            'weight': 0.5,
            'price': 12000,
            'status': 'доставлен',
            'cargoType': 'документы',
            'timestamp': datetime.now() - timedelta(days=1),
            'contact': '+7 (900) 456-78-90',
            'description': 'Срочные документы курьерской доставкой',
            'urgent': False
        },
        {
            'from': 'Ростов-на-Дону',
            'to': 'Краснодар',
            'weight': 8.0,
            'price': 60000,
            'status': 'активный',
            'cargoType': 'продукты',
            'timestamp': datetime.now() - timedelta(hours=12),
            'contact': '+7 (900) 567-89-01',
            'description': 'Замороженные продукты, рефрижератор',
            'urgent': True
        }
    ]
    
    cargos_collection = db.collection('cargos')
    
    for i, cargo_data in enumerate(test_cargos, 1):
        try:
            doc_ref = cargos_collection.add(cargo_data)
            print(f"✅ Груз {i} создан: {doc_ref[1].id}")
        except Exception as e:
            print(f"❌ Ошибка создания груза {i}: {str(e)}")

def create_test_statistics(db):
    """Создание тестовой статистики"""
    print("\n📊 Создаем тестовую статистику...")
    
    stats_data = {
        'totalMessages': 4,
        'processedMessages': 2,
        'totalCargos': 5,
        'activeCargos': 3,
        'totalRevenue': 222000,
        'lastUpdated': datetime.now(),
        'averageWeight': 5.1,
        'topRoutes': [
            {'route': 'Москва - СПб', 'count': 1},
            {'route': 'Екатеринбург - Челябинск', 'count': 1},
            {'route': 'Новосибирск - Омск', 'count': 1}
        ]
    }
    
    try:
        db.collection('statistics').document('main').set(stats_data)
        print("✅ Статистика создана")
    except Exception as e:
        print(f"❌ Ошибка создания статистики: {str(e)}")

def main():
    """Основная функция"""
    print("🚀 Запуск создания тестовых данных для Autologist...")
    print("=" * 50)
    
    # Инициализация Firebase
    db = initialize_firebase()
    if db is None:
        return
    
    try:
        # Создание тестовых данных
        create_test_messages(db)
        create_test_cargos(db)
        create_test_statistics(db)
        
        print("\n" + "=" * 50)
        print("🎉 Все тестовые данные успешно созданы!")
        print("\n📋 Что было создано:")
        print("• 4 тестовых сообщения в коллекции 'messages'")
        print("• 5 тестовых грузов в коллекции 'cargos'") 
        print("• Статистика в коллекции 'statistics'")
        print("\n💡 Теперь можете:")
        print("1. Обновить страницу веб-интерфейса")
        print("2. Проверить отображение данных")
        print("3. Протестировать функции поиска и фильтрации")
        
    except Exception as e:
        print(f"\n❌ Общая ошибка: {str(e)}")

if __name__ == "__main__":
    main()