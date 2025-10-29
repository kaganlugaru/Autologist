"""
Упрощенный скрипт для создания тестовых данных через Firebase REST API
Работает без дополнительной аутентификации
"""

import requests
import json
from datetime import datetime, timedelta

# Конфигурация проекта Firebase
PROJECT_ID = "autologist-91ecf"
BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

def create_test_messages():
    """Создание тестовых сообщений"""
    print("\n📨 Создаем тестовые сообщения...")
    
    test_messages = [
        {
            "fields": {
                "text": {"stringValue": "Нужно перевезти груз из Москвы в СПб, 5 тонн, срочно до завтра"},
                "source": {"stringValue": "telegram"},
                "timestamp": {"timestampValue": datetime.now().isoformat() + "Z"},
                "processed": {"booleanValue": False},
                "chat_id": {"stringValue": "chat_123"},
                "message_id": {"stringValue": "msg_001"}
            }
        },
        {
            "fields": {
                "text": {"stringValue": "Ищу транспорт для перевозки мебели Екатеринбург -> Челябинск, 2 тонны"},
                "source": {"stringValue": "whatsapp"},
                "timestamp": {"timestampValue": (datetime.now() - timedelta(hours=2)).isoformat() + "Z"},
                "processed": {"booleanValue": True},
                "chat_id": {"stringValue": "chat_456"},
                "message_id": {"stringValue": "msg_002"}
            }
        },
        {
            "fields": {
                "text": {"stringValue": "Есть груз 10 тонн металлопроката, Новосибирск - Омск, оплата сразу"},
                "source": {"stringValue": "telegram"},
                "timestamp": {"timestampValue": (datetime.now() - timedelta(hours=5)).isoformat() + "Z"},
                "processed": {"booleanValue": False},
                "chat_id": {"stringValue": "chat_789"},
                "message_id": {"stringValue": "msg_003"}
            }
        },
        {
            "fields": {
                "text": {"stringValue": "Нужна газель для перевозки коробок по городу, 500 кг максимум"},
                "source": {"stringValue": "whatsapp"},
                "timestamp": {"timestampValue": (datetime.now() - timedelta(hours=8)).isoformat() + "Z"},
                "processed": {"booleanValue": True},
                "chat_id": {"stringValue": "chat_101"},
                "message_id": {"stringValue": "msg_004"}
            }
        }
    ]
    
    for i, message_data in enumerate(test_messages, 1):
        try:
            response = requests.post(
                f"{BASE_URL}/messages",
                headers={"Content-Type": "application/json"},
                data=json.dumps(message_data)
            )
            if response.status_code == 200:
                print(f"✅ Сообщение {i} создано")
            else:
                print(f"❌ Ошибка создания сообщения {i}: {response.status_code}")
                print(f"   Ответ: {response.text}")
        except Exception as e:
            print(f"❌ Ошибка сообщения {i}: {str(e)}")

def create_test_cargos():
    """Создание тестовых грузов"""
    print("\n📦 Создаем тестовые грузы...")
    
    test_cargos = [
        {
            "fields": {
                "from": {"stringValue": "Москва"},
                "to": {"stringValue": "Санкт-Петербург"},
                "weight": {"doubleValue": 5.0},
                "price": {"integerValue": "45000"},
                "status": {"stringValue": "активный"},
                "cargoType": {"stringValue": "стройматериалы"},
                "timestamp": {"timestampValue": datetime.now().isoformat() + "Z"},
                "contact": {"stringValue": "+7 (900) 123-45-67"},
                "description": {"stringValue": "Кирпич и цемент для стройки"},
                "urgent": {"booleanValue": True}
            }
        },
        {
            "fields": {
                "from": {"stringValue": "Екатеринбург"},
                "to": {"stringValue": "Челябинск"},
                "weight": {"doubleValue": 2.0},
                "price": {"integerValue": "25000"},
                "status": {"stringValue": "в пути"},
                "cargoType": {"stringValue": "мебель"},
                "timestamp": {"timestampValue": (datetime.now() - timedelta(hours=3)).isoformat() + "Z"},
                "contact": {"stringValue": "+7 (900) 234-56-78"},
                "description": {"stringValue": "Офисная мебель (столы, стулья)"},
                "urgent": {"booleanValue": False}
            }
        },
        {
            "fields": {
                "from": {"stringValue": "Новосибирск"},
                "to": {"stringValue": "Омск"},
                "weight": {"doubleValue": 10.0},
                "price": {"integerValue": "80000"},
                "status": {"stringValue": "активный"},
                "cargoType": {"stringValue": "металлопрокат"},
                "timestamp": {"timestampValue": (datetime.now() - timedelta(hours=6)).isoformat() + "Z"},
                "contact": {"stringValue": "+7 (900) 345-67-89"},
                "description": {"stringValue": "Листовая сталь и профиль"},
                "urgent": {"booleanValue": True}
            }
        },
        {
            "fields": {
                "from": {"stringValue": "Казань"},
                "to": {"stringValue": "Самара"},
                "weight": {"doubleValue": 0.5},
                "price": {"integerValue": "12000"},
                "status": {"stringValue": "доставлен"},
                "cargoType": {"stringValue": "документы"},
                "timestamp": {"timestampValue": (datetime.now() - timedelta(days=1)).isoformat() + "Z"},
                "contact": {"stringValue": "+7 (900) 456-78-90"},
                "description": {"stringValue": "Срочные документы курьерской доставкой"},
                "urgent": {"booleanValue": False}
            }
        },
        {
            "fields": {
                "from": {"stringValue": "Ростов-на-Дону"},
                "to": {"stringValue": "Краснодар"},
                "weight": {"doubleValue": 8.0},
                "price": {"integerValue": "60000"},
                "status": {"stringValue": "активный"},
                "cargoType": {"stringValue": "продукты"},
                "timestamp": {"timestampValue": (datetime.now() - timedelta(hours=12)).isoformat() + "Z"},
                "contact": {"stringValue": "+7 (900) 567-89-01"},
                "description": {"stringValue": "Замороженные продукты, рефрижератор"},
                "urgent": {"booleanValue": True}
            }
        }
    ]
    
    for i, cargo_data in enumerate(test_cargos, 1):
        try:
            response = requests.post(
                f"{BASE_URL}/cargos",
                headers={"Content-Type": "application/json"},
                data=json.dumps(cargo_data)
            )
            if response.status_code == 200:
                print(f"✅ Груз {i} создан")
            else:
                print(f"❌ Ошибка создания груза {i}: {response.status_code}")
                print(f"   Ответ: {response.text}")
        except Exception as e:
            print(f"❌ Ошибка груза {i}: {str(e)}")

def main():
    """Основная функция"""
    print("🚀 Запуск создания тестовых данных для Autologist...")
    print("=" * 50)
    print(f"📡 Подключение к проекту: {PROJECT_ID}")
    
    try:
        # Создание тестовых данных
        create_test_messages()
        create_test_cargos()
        
        print("\n" + "=" * 50)
        print("🎉 Скрипт завершен!")
        print("\n📋 Попытка создания:")
        print("• 4 тестовых сообщения в коллекции 'messages'")
        print("• 5 тестовых грузов в коллекции 'cargos'")
        print("\n💡 Теперь:")
        print("1. Обновите страницу веб-интерфейса (F5)")
        print("2. Проверьте отображение данных")
        print("3. Если данные не появились, проверьте Firebase Console")
        
    except Exception as e:
        print(f"\n❌ Общая ошибка: {str(e)}")

if __name__ == "__main__":
    main()