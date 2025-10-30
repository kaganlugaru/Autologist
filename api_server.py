"""
API сервер для управления Autologist системой
Предоставляет REST API для веб-интерфейса
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import os
import subprocess
import psutil
from datetime import datetime
import threading
import time

app = Flask(__name__)
CORS(app)

class AutologistAPI:
    def __init__(self):
        self.parser_process = None
        self.config_file = 'config/monitored_chats.json'
        self.stats = {
            'parser_status': 'stopped',
            'last_update': None,
            'total_messages': 0,
            'errors': 0
        }
    
    def load_chats_config(self):
        """Загрузка конфигурации чатов из Firestore"""
        try:
            from google.cloud import firestore
            db = firestore.Client()
            chats_ref = db.collection('monitored_chats')
            chats = [doc.to_dict() for doc in chats_ref.stream()]
            return chats
        except Exception as e:
            print(f"Ошибка загрузки конфигурации из Firestore: {e}")
            return []
    
    def save_chats_config(self, config):
        """Сохранение конфигурации чатов"""
        try:
            os.makedirs('config', exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    def get_parser_status(self):
        """Проверка статуса парсера"""
        try:
            # Проверяем запущенные процессы Python
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'telegram_parser_v2.py' in cmdline:
                            return {
                                'status': 'running',
                                'pid': proc.info['pid'],
                                'uptime': time.time() - proc.create_time()
                            }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {'status': 'stopped'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def start_parser(self):
        """Запуск парсера"""
        try:
            # Проверяем что парсер не запущен
            status = self.get_parser_status()
            if status['status'] == 'running':
                return {'success': False, 'message': 'Парсер уже запущен'}
            
            # Запускаем парсер в фоне
            self.parser_process = subprocess.Popen([
                'python', 'parsers/telegram_parser_v2.py'
            ], cwd=os.getcwd())
            
            time.sleep(2)  # Ждем немного для запуска
            
            return {'success': True, 'message': 'Парсер запущен', 'pid': self.parser_process.pid}
        except Exception as e:
            return {'success': False, 'message': f'Ошибка запуска: {str(e)}'}
    
    def stop_parser(self):
        """Остановка парсера"""
        try:
            stopped = False
            
            # Ищем и останавливаем все процессы парсера
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'telegram_parser_v2.py' in cmdline:
                            proc.terminate()
                            proc.wait(timeout=5)
                            stopped = True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
            
            if stopped:
                return {'success': True, 'message': 'Парсер остановлен'}
            else:
                return {'success': False, 'message': 'Парсер не был запущен'}
                
        except Exception as e:
            return {'success': False, 'message': f'Ошибка остановки: {str(e)}'}

    def get_all_user_chats(self):
        """Получить все чаты пользователя из Telegram"""
        try:
            import asyncio
            from telethon import TelegramClient
            import json
            
            # Проверяем наличие конфигурации
            if not os.path.exists('config/telegram_config.json'):
                print("Конфигурация Telegram не найдена")
                return self._get_test_chats()  # Возвращаем тестовые данные
            
            # Чтение конфигурации
            with open('config/telegram_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Проверяем что конфигурация заполнена
            if config.get('api_id') == 'YOUR_API_ID' or not config.get('api_id'):
                print("Telegram API не настроен")
                return self._get_test_chats()  # Возвращаем тестовые данные
            
            async def fetch_real_chats():
                try:
                    client = TelegramClient('autologist_session', config['api_id'], config['api_hash'])
                    await client.start()  # Запросит код и будет ждать ввода в терминале
                    all_chats = []
                    monitored_chats = self.load_chats_config()
                    monitored_ids = [str(chat['chat_id']) for chat in monitored_chats]
                    print("Получаем список чатов из Telegram...")
                    async for dialog in client.iter_dialogs():
                        # Только групповые чаты и каналы
                        if dialog.is_group or dialog.is_channel:
                            chat_info = {
                                'id': str(dialog.id),
                                'title': dialog.name,
                                'username': getattr(dialog.entity, 'username', None),
                                'type': 'channel' if dialog.is_channel else 'supergroup',
                                'participants_count': getattr(dialog.entity, 'participants_count', 0),
                                'is_monitored': str(dialog.id) in monitored_ids
                            }
                            all_chats.append(chat_info)
                    await client.disconnect()
                    print(f"Найдено {len(all_chats)} групповых чатов")
                    return all_chats
                except Exception as e:
                    print(f"Ошибка подключения к Telegram: {e}")
                    return self._get_test_chats()
            # Запускаем асинхронную функцию
            return asyncio.run(fetch_real_chats())
            
        except Exception as e:
            print(f"Ошибка получения чатов: {e}")
            return self._get_test_chats()
    
    def _get_test_chats(self):
        """Возвращаем пустой список вместо тестовых данных"""
        return []

    def add_chat_to_monitoring(self, chat_id, name, username=None, keywords=None):
        """Добавить чат в мониторинг"""
        try:
            monitored_chats = self.load_chats_config()
            
            # Проверяем, не добавлен ли уже
            if any(chat['chat_id'] == chat_id for chat in monitored_chats):
                return {'success': False, 'message': 'Чат уже добавлен в мониторинг'}
            
            # Базовые ключевые слова по умолчанию
            default_keywords = [
                "груз", "перевозка", "доставка", "транспорт", "тонн", "маршрут"
            ]
            
            new_chat = {
                'title': name if name else f'Чат {chat_id}',
                'username': username,
                'chat_id': str(chat_id),
                'keywords': keywords if keywords else default_keywords,
                'enabled': True
            }
            
            monitored_chats.append(new_chat)
            
            # Сохраняем
            if self.save_chats_config(monitored_chats):
                return {'success': True, 'message': 'Чат успешно добавлен в мониторинг'}
            else:
                return {'success': False, 'message': 'Ошибка сохранения конфигурации'}
            
        except Exception as e:
            return {'success': False, 'message': f'Ошибка добавления чата: {str(e)}'}

    def remove_chat_from_monitoring(self, chat_id):
        """Удалить чат из мониторинга"""
        try:
            monitored_chats = self.load_chats_config()
            
            # Находим и удаляем чат
            original_count = len(monitored_chats)
            monitored_chats = [chat for chat in monitored_chats if chat['chat_id'] != chat_id]
            
            if len(monitored_chats) == original_count:
                return {'success': False, 'message': 'Чат не найден в мониторинге'}
            
            # Сохраняем
            if self.save_chats_config(monitored_chats):
                return {'success': True, 'message': 'Чат удален из мониторинга'}
            else:
                return {'success': False, 'message': 'Ошибка сохранения конфигурации'}
            
        except Exception as e:
            return {'success': False, 'message': f'Ошибка удаления чата: {str(e)}'}

    def update_chat_keywords(self, chat_id, keywords):
        """Обновить ключевые слова для чата"""
        try:
            monitored_chats = self.load_chats_config()
            
            # Находим чат и обновляем ключевые слова
            for chat in monitored_chats:
                if chat['chat_id'] == chat_id:
                    chat['keywords'] = keywords
                    break
            else:
                return {'success': False, 'message': 'Чат не найден'}
            
            # Сохраняем
            if self.save_chats_config(monitored_chats):
                return {'success': True, 'message': 'Ключевые слова обновлены'}
            else:
                return {'success': False, 'message': 'Ошибка сохранения конфигурации'}
            
        except Exception as e:
            return {'success': False, 'message': f'Ошибка обновления: {str(e)}'}

    def toggle_chat_monitoring(self, chat_id, enabled):
        """Включить/отключить мониторинг чата"""
        try:
            monitored_chats = self.load_chats_config()
            
            # Находим чат и обновляем статус
            for chat in monitored_chats:
                if chat['chat_id'] == chat_id:
                    chat['enabled'] = enabled
                    break
            else:
                return {'success': False, 'message': 'Чат не найден'}
            
            # Сохраняем
            if self.save_chats_config(monitored_chats):
                return {'success': True, 'message': f'Мониторинг чата {"включен" if enabled else "отключен"}'}
            else:
                return {'success': False, 'message': 'Ошибка сохранения конфигурации'}
            
        except Exception as e:
            return {'success': False, 'message': f'Ошибка изменения статуса: {str(e)}'}

# Создаем экземпляр API
autologist_api = AutologistAPI()

# Статические файлы
@app.route('/')
def index():
    return send_from_directory('frontend', 'dashboard.html')

@app.route('/frontend/<path:filename>')
def frontend_files(filename):
    return send_from_directory('frontend', filename)

@app.route('/config/<path:filename>')
def config_files(filename):
    return send_from_directory('config', filename)

# API endpoints

from google.cloud import firestore
from datetime import datetime, timedelta

@app.route('/api/status')
def get_status():
    """Получение общего статуса системы из Firestore"""
    parser_status = autologist_api.get_parser_status()
    try:
        db = firestore.Client()
        # Считаем количество сообщений в Firestore
        total_messages = len([doc for doc in db.collection('messages').stream()])
    except Exception as e:
        print(f"[STAT] Ошибка получения total_messages из Firestore: {e}")
        total_messages = -1
    try:
        today = datetime.utcnow().date()
        today_start = datetime(today.year, today.month, today.day)
        today_end = today_start + timedelta(days=1)
        today_messages = len([
            doc for doc in db.collection('messages')
            .where('timestamp', '>=', today_start.isoformat())
            .where('timestamp', '<', today_end.isoformat())
            .stream()
        ])
    except Exception as e:
        print(f"[STAT] Ошибка получения today_messages из Firestore: {e}")
        today_messages = -1
    try:
        chats_ref = db.collection('monitored_chats')
        chats = [doc.to_dict() for doc in chats_ref.stream()]
        total_chats = len(chats)
        active_chats = len([c for c in chats if c.get('enabled', True)])
    except Exception as e:
        print(f"[STAT] Ошибка получения monitored_chats из Firestore: {e}")
        total_chats = -1
        active_chats = -1
    return jsonify({
        'parser_status': parser_status.get('status', 'stopped'),
        'total_chats': total_chats,
        'active_chats': active_chats,
        'total_messages': total_messages,
        'today_messages': today_messages,
        'error_count': 0,
        'parser': parser_status,
        'firebase': {'status': 'connected'},
        'ai': {'status': 'disabled'}
    })

@app.route('/api/chats')
def get_chats():
    """Получение списка чатов"""
    chats = autologist_api.load_chats_config()
    
    # Добавляем статистику для каждого чата
    for chat in chats:
        chat['message_count'] = 0  # TODO: подсчет сообщений по чату
        chat['last_message'] = None  # TODO: последнее сообщение
    
    return jsonify(chats)

@app.route('/api/chats/<chat_id>/toggle', methods=['POST'])
def toggle_chat(chat_id):
    """Включение/выключение чата"""
    try:
        data = request.json
        enabled = data.get('enabled', False)
        
        chats = autologist_api.load_chats_config()
        
        for chat in chats:
            if str(chat['chat_id']) == str(chat_id):
                chat['enabled'] = enabled
                break
        
        if autologist_api.save_chats_config(chats):
            return jsonify({'success': True, 'message': f'Чат {"включен" if enabled else "выключен"}'})
        else:
            return jsonify({'success': False, 'message': 'Ошибка сохранения'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/parser/start', methods=['POST'])
def start_parser():
    """Запуск парсера"""
    result = autologist_api.start_parser()
    return jsonify(result)

@app.route('/api/parser/stop', methods=['POST'])
def stop_parser():
    """Остановка парсера"""
    result = autologist_api.stop_parser()
    return jsonify(result)

@app.route('/api/telegram/verify', methods=['POST'])
def verify_telegram_code():
    """Ввод кода подтверждения Telegram"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        
        if not code:
            return jsonify({'success': False, 'message': 'Код не указан'})
        
        # Здесь должна быть логика проверки кода
        # Пока возвращаем успех для любого 5-значного кода
        if len(code) == 5 and code.isdigit():
            return jsonify({'success': True, 'message': 'Код принят, подключение к Telegram установлено'})
        else:
            return jsonify({'success': False, 'message': 'Неверный формат кода. Введите 5-значный код'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

from google.cloud import firestore

@app.route('/api/messages')
def get_messages():
    """Получение списка сообщений из Firestore"""
    try:
        db = firestore.Client()
        limit = request.args.get('limit', 50, type=int)
        messages_ref = db.collection('messages').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        docs = messages_ref.stream()
        messages = [doc.to_dict() for doc in docs]
        return jsonify(messages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/recent')
def get_recent_messages():
    """Получение последних сообщений из Firestore"""
    try:
        db = firestore.Client()
        messages_ref = db.collection('messages').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(20)
        docs = messages_ref.stream()
        messages = [doc.to_dict() for doc in docs]
        return jsonify(messages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def search_messages():
    """Поиск сообщений"""
    try:
        query = request.args.get('q', '').lower()
        chat_filter = request.args.get('chat_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        messages = []
        
        # Читаем все сообщения
        if os.path.exists('data/messages'):
            for filename in os.listdir('data/messages'):
                if filename.endswith('.json'):
                    try:
                        with open(f'data/messages/{filename}', 'r', encoding='utf-8') as f:
                            message = json.load(f)
                            
                            # Фильтрация по тексту
                            if query and query not in message.get('text', '').lower():
                                continue
                            
                            # Фильтрация по чату
                            if chat_filter and str(message.get('chat_id')) != str(chat_filter):
                                continue
                            
                            # TODO: Фильтрация по дате
                            
                            messages.append(message)
                    except Exception:
                        continue
        
        # Сортируем по времени
        messages.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify(messages)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Новые API endpoints для управления чатами

@app.route('/api/chats/monitored')
def get_monitored_chats():
    """Получение отслеживаемых чатов"""
    try:
        chats_config = autologist_api.load_chats_config()
        return jsonify({
            'success': True,
            'chats': chats_config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chats/all')
def get_all_chats():
    """Получение всех доступных чатов пользователя"""
    try:
        all_chats = autologist_api.get_all_user_chats()
        return jsonify(all_chats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chats/add', methods=['POST'])
def add_chat():
    """Добавление чата в мониторинг"""
    try:
        data = request.json
        chat_id = data.get('chat_id')
        keywords = data.get('keywords', [])
        
        if not chat_id:
            return jsonify({'success': False, 'message': 'Не указан ID чата'}), 400
        
        # Получаем название чата из списка всех чатов
        all_chats = autologist_api.get_all_user_chats()
        chat_name = None
        chat_username = None
        
        for chat in all_chats:
            if str(chat['id']) == str(chat_id):
                chat_name = chat.get('title', chat.get('name', f'Чат {chat_id}'))
                chat_username = chat.get('username')
                break
        
        if not chat_name:
            chat_name = f'Чат {chat_id}'
        
        result = autologist_api.add_chat_to_monitoring(chat_id, chat_name, chat_username, keywords)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/chats/<chat_id>/remove', methods=['DELETE'])
def remove_chat(chat_id):
    """Удаление чата из мониторинга"""
    try:
        result = autologist_api.remove_chat_from_monitoring(int(chat_id))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/chats/remove', methods=['POST'])
def remove_chat_post():
    """Удаление чата из мониторинга (POST метод)"""
    try:
        data = request.json
        chat_id = data.get('chat_id')
        if not chat_id:
            return jsonify({'success': False, 'message': 'chat_id обязателен'}), 400
        
        result = autologist_api.remove_chat_from_monitoring(str(chat_id))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/chats/<chat_id>/keywords', methods=['PUT'])
def update_keywords(chat_id):
    """Обновление ключевых слов чата"""
    try:
        data = request.json
        keywords = data.get('keywords', [])
        
        result = autologist_api.update_chat_keywords(int(chat_id), keywords)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/chats/<chat_id>/toggle', methods=['PUT'])
def toggle_chat_monitoring(chat_id):
    """Включение/отключение мониторинга чата"""
    try:
        data = request.json
        enabled = data.get('enabled', False)
        
        result = autologist_api.toggle_chat_monitoring(int(chat_id), enabled)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    print("🚛 Autologist API Server")
    print("=" * 40)
    print("🌐 Интерфейс: http://localhost:8080")
    print("📡 API: http://localhost:8080/api/")
    print("🔧 Управление парсером через веб-интерфейс")
    print()
    
    app.run(host='0.0.0.0', port=8080, debug=True)