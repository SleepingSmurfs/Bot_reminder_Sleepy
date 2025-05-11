import os
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('db_errors.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class JSONDatabase:
    def __init__(self, file_path: str = 'data.json'):
        self.file_path = file_path
        self.data = {
            'users': {},
            'reminders': {},
            'deleted_reminders': [],
            'last_reminder_id': 0
        }
        self.load_data()
        
    def load_data(self) -> None:
        """Загружает данные из JSON файла"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info("Данные успешно загружены из JSON файла")
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных: {e}")
            self.save_data()

    def save_data(self) -> bool:
        """Сохраняет данные в JSON файл"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных: {e}")
            return False

    def add_user(self, user_id: int, username: str, first_name: str, last_name: str) -> bool:
        """Добавляет пользователя"""
        self.data['users'][str(user_id)] = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'registered_at': datetime.now().isoformat()
        }
        return self.save_data()

    def add_reminder(self, user_id: int, text: str, priority: int, days: int) -> Optional[int]:
        """Добавляет напоминание и возвращает его ID"""
        reminder_id = self.data['last_reminder_id'] + 1
        expires_at = datetime.now() + timedelta(days=days)
        
        self.data['reminders'][str(reminder_id)] = {
            'user_id': user_id,
            'text': text,
            'priority': priority,
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat(),
            'is_completed': False
        }
        self.data['last_reminder_id'] = reminder_id
        
        if self.save_data():
            return reminder_id
        return None

    def get_today_reminders(self, user_id: int) -> List[Dict[str, Any]]:
        """Возвращает напоминания на сегодня"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        result = []
        
        for reminder_id, reminder in self.data['reminders'].items():
            expires_at = datetime.fromisoformat(reminder['expires_at']).date()
            if (reminder['user_id'] == user_id and 
                today <= expires_at < tomorrow and 
                not reminder['is_completed']):
                result.append({
                    'id': int(reminder_id),
                    'text': reminder['text'],
                    'priority': reminder['priority']
                })
        
        return sorted(result, key=lambda x: x['priority'], reverse=True)

    def get_all_users(self) -> List[int]:
        """Возвращает список всех пользователей"""
        return [int(user_id) for user_id in self.data['users'].keys()]

    def delete_reminder(self, reminder_id: int, user_id: int, reason: str = "Пользователь удалил") -> bool:
        """Удаляет напоминание с сохранением в истории"""
        reminder_key = str(reminder_id)
        if reminder_key not in self.data['reminders']:
            return False
            
        reminder = self.data['reminders'][reminder_key]
        if reminder['user_id'] != user_id:
            return False
            
        self.data['deleted_reminders'].append({
            'original_id': reminder_id,
            'user_id': user_id,
            'text': reminder['text'],
            'priority': reminder['priority'],
            'created_at': reminder['created_at'],
            'deleted_at': datetime.now().isoformat(),
            'reason': reason
        })
        
        del self.data['reminders'][reminder_key]
        
        return self.save_data()

    def get_deleted_reminders(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Возвращает историю удаленных напоминаний"""
        user_deleted = [
            r for r in self.data['deleted_reminders'] 
            if r['user_id'] == user_id
        ]
        user_deleted.sort(key=lambda x: x['deleted_at'], reverse=True)
        return user_deleted[:limit]

    def delete_old_reminders(self) -> bool:
        """Удаляет старые напоминания и чистит историю"""
        now = datetime.now()
        month_ago = now - timedelta(days=30)
        
        for reminder_id, reminder in list(self.data['reminders'].items()):
            expires_at = datetime.fromisoformat(reminder['expires_at'])
            if expires_at < now:
                self.data['deleted_reminders'].append({
                    'original_id': int(reminder_id),
                    'user_id': reminder['user_id'],
                    'text': reminder['text'],
                    'priority': reminder['priority'],
                    'created_at': reminder['created_at'],
                    'deleted_at': datetime.now().isoformat(),
                    'reason': 'Автоматическое удаление (истек срок)'
                })
                del self.data['reminders'][reminder_id]
        
        self.data['deleted_reminders'] = [
            r for r in self.data['deleted_reminders']
            if datetime.fromisoformat(r['deleted_at']) >= month_ago
        ]
        
        logger.info("Очистка старых напоминаний выполнена")
        return self.save_data()

    def close(self) -> None:
        """Закрывает соединение (для совместимости)"""
        self.save_data()
        logger.info("Данные сохранены при закрытии")