# Скрипт для переноса monitored_chats.json в Firestore
# Просто запустите: python migrate_monitored_chats_to_firestore.py

import json
from google.cloud import firestore

# Путь к monitored_chats.json
MONITORED_CHATS_PATH = 'config/monitored_chats.json'

print('⏳ Подключение к Firestore...')
db = firestore.Client()
print('✅ Firestore готов')

with open(MONITORED_CHATS_PATH, 'r', encoding='utf-8') as f:
    chats = json.load(f)

count = 0
for chat in chats:
    doc_id = str(chat.get('chat_id'))
    db.collection('monitored_chats').document(doc_id).set(chat)
    count += 1

print(f'✅ Перенос завершён. Загружено чатов: {count}')
