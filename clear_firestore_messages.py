# Скрипт для удаления всех сообщений из коллекции Firestore
# Просто запустите: python clear_firestore_messages.py

from google.cloud import firestore

print('⏳ Подключение к Firestore...')
db = firestore.Client()
print('✅ Firestore готов')

messages_ref = db.collection('messages')
docs = messages_ref.stream()
count = 0
for doc in docs:
    doc.reference.delete()
    count += 1

print(f'✅ Удалено сообщений: {count}')
