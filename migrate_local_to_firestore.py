# Скрипт для переноса всех локальных сообщений в Firestore
# Просто запустите: python migrate_local_to_firestore.py

import os
import json
from google.cloud import firestore

# Папка с локальными сообщениями
LOCAL_MESSAGES_DIR = 'data/messages'

# Инициализация Firestore
print('⏳ Подключение к Firestore...')
db = firestore.Client()
print('✅ Firestore готов')

count = 0

if os.path.exists(LOCAL_MESSAGES_DIR):
    for filename in os.listdir(LOCAL_MESSAGES_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(LOCAL_MESSAGES_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    message = json.load(f)
                # Проверяем, нет ли уже такого сообщения (по id или timestamp+chat_id)
                # Можно доработать под вашу структуру
                doc_id = message.get('id') or f"{message.get('chat_id','')}_{message.get('timestamp','')}"
                db.collection('messages').document(doc_id).set(message)
                count += 1
            except Exception as e:
                print(f'Ошибка при обработке {filename}: {e}')
else:
    print('Папка с локальными сообщениями не найдена!')

print(f'✅ Перенос завершён. Загружено сообщений: {count}')
