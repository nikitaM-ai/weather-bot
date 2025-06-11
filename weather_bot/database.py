import json
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class NotificationDB:
    def __init__(self, file_path: str = 'notifications.json'):
        self.file_path = file_path
        self._init_db()

    def _init_db(self):
        try:
            if not os.path.exists(self.file_path):
                with open(self.file_path, 'w') as f:
                    json.dump({}, f)
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {str(e)}")
            raise

    def get_all_notifications(self) -> Dict:
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка чтения БД: {str(e)}")
            return {}

    def save_notification(self, chat_id: int, city: str, time_str: str) -> bool:
        try:
            data = self.get_all_notifications()
            data[str(chat_id)] = {'city': city, 'time': time_str}
            
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения уведомления: {str(e)}")
            return False

    def delete_notification(self, chat_id: int) -> bool:
        try:
            data = self.get_all_notifications()
            if str(chat_id) in data:
                del data[str(chat_id)]
                with open(self.file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка удаления уведомления: {str(e)}")
            return False

    def get_notification(self, chat_id: int) -> Optional[Dict]:
        try:
            data = self.get_all_notifications()
            return data.get(str(chat_id))
        except Exception as e:
            logger.error(f"Ошибка получения уведомления: {str(e)}")
            return None