"""
Простой скрипт для создания тестовых данных в Firestore
Использует веб-API Firebase вместо Admin SDK
"""

import json
import requests
from datetime import datetime

# Настройки Firebase из .env файла
FIREBASE_PROJECT_ID = "autologist-65cd7"
FIREBASE_API_KEY = "AIzaSyA8q_Dl-rKdm-MUr4226czsIRjioBGEChY"

def create_test_data():
    """Создание тестовых данных через REST API"""
    
    print("🔥 Создание тестовых данных в Firestore...")
    print(f"📊 Проект: {FIREBASE_PROJECT_ID}")
    print("-" * 50)
    
    # Базовый URL для Firestore REST API
    base_url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents"
    
    # Тестовые сырые сообщения
    test_messages = [
        {
            "text": {"stringValue": "Везу мебель Москва-Питер, 5 тонн, 40000 руб, тел 89991234567"},
            "timestamp": {"timestampValue": datetime.now().isoformat() + "Z"},
            "chat_id": {"integerValue": "-1001234567890"},
            "chat_title": {"stringValue": "Грузы Москва-СПб"},
            "sender_id": {"integerValue": "123456789"},
            "message_id": {"integerValue": "1001"},
            "hash": {"stringValue": "sample_hash_1"},
            "processed": {"booleanValue": False},
            "has_media": {"booleanValue": False}
        },
        {
            "text": {"stringValue": "Нужен транспорт: Новосибирск → Екатеринбург, продукты, 3т, срочно!"},
            "timestamp": {"timestampValue": datetime.now().isoformat() + "Z"},
            "chat_id": {"integerValue": "-1001234567891"},
            "chat_title": {"stringValue": "Сибирские грузы"},
            "sender_id": {"integerValue": "987654321"},
            "message_id": {"integerValue": "1002"},
            "hash": {"stringValue": "sample_hash_2"},
            "processed": {"booleanValue": True},
            "has_media": {"booleanValue": False}
        },
        {
            "text": {"stringValue": "Стройматериалы Казань-Самара, 8 тонн, тент, 60к"},
            "timestamp": {"timestampValue": datetime.now().isoformat() + "Z"},
            "chat_id": {"integerValue": "-1001234567892"},
            "chat_title": {"stringValue": "Поволжье логистика"},
            "sender_id": {"integerValue": "555666777"},
            "message_id": {"integerValue": "1003"},
            "hash": {"stringValue": "sample_hash_3"},
            "processed": {"booleanValue": True},
            "has_media": {"booleanValue": False}
        }
    ]
    
    # Тестовые обработанные грузы
    test_cargos = [
        {
            "from_city": {"stringValue": "Москва"},
            "to_city": {"stringValue": "Санкт-Петербург"},
            "cargo_type": {"stringValue": "мебель"},
            "weight": {"stringValue": "5 тонн"},
            "volume": {"stringValue": "не указан"},
            "price": {"stringValue": "40000 руб"},
            "contact": {"stringValue": "89991234567"},
            "urgency": {"stringValue": "обычная"},
            "timestamp": {"timestampValue": datetime.now().isoformat() + "Z"},
            "original_message_id": {"stringValue": "sample_hash_1"},
            "status": {"stringValue": "новый"}
        },
        {
            "from_city": {"stringValue": "Новосибирск"},
            "to_city": {"stringValue": "Екатеринбург"},
            "cargo_type": {"stringValue": "продукты"},
            "weight": {"stringValue": "3 тонны"},
            "volume": {"stringValue": "не указан"},
            "price": {"stringValue": "договорная"},
            "contact": {"stringValue": "не указан"},
            "urgency": {"stringValue": "высокая"},
            "timestamp": {"timestampValue": datetime.now().isoformat() + "Z"},
            "original_message_id": {"stringValue": "sample_hash_2"},
            "status": {"stringValue": "в работе"}
        },
        {
            "from_city": {"stringValue": "Казань"},
            "to_city": {"stringValue": "Самара"},
            "cargo_type": {"stringValue": "стройматериалы"},
            "weight": {"stringValue": "8 тонн"},
            "volume": {"stringValue": "тент"},
            "price": {"stringValue": "60000 руб"},
            "contact": {"stringValue": "не указан"},
            "urgency": {"stringValue": "обычная"},
            "timestamp": {"timestampValue": datetime.now().isoformat() + "Z"},
            "original_message_id": {"stringValue": "sample_hash_3"},
            "status": {"stringValue": "новый"}
        }
    ]
    
    try:
        # Добавляем сырые сообщения
        print("📝 Добавляем тестовые сообщения...")
        for i, message in enumerate(test_messages):
            url = f"{base_url}/raw_messages?key={FIREBASE_API_KEY}"
            
            response = requests.post(url, json={"fields": message})
            
            if response.status_code == 200:
                print(f"✅ Добавлено сообщение {i+1}")
            else:
                print(f"❌ Ошибка добавления сообщения {i+1}: {response.text}")
        
        # Добавляем обработанные грузы
        print("\n📦 Добавляем тестовые грузы...")
        for i, cargo in enumerate(test_cargos):
            url = f"{base_url}/processed_cargos?key={FIREBASE_API_KEY}"
            
            response = requests.post(url, json={"fields": cargo})
            
            if response.status_code == 200:
                print(f"✅ Добавлен груз {i+1}")
            else:
                print(f"❌ Ошибка добавления груза {i+1}: {response.text}")
        
        print("\n🎉 Тестовые данные успешно созданы!")
        print("🌐 Обновите веб-интерфейс (http://localhost:8000) чтобы увидеть данные")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\n💡 Убедитесь что:")
        print("1. Проект Firebase настроен правильно")
        print("2. Firestore Database создан")
        print("3. Правила безопасности разрешают запись")

if __name__ == "__main__":
    create_test_data()