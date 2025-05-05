import os
import time
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('db_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn = None
        self.connect()
        
    def connect(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.conn = psycopg2.connect(
                    dbname=os.getenv('DB_NAME'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD'),
                    host=os.getenv('DB_HOST'),
                    port=os.getenv('DB_PORT'),
                    connect_timeout=5
                )
                self.create_tables()
                logger.info("Успешное подключение к базе данных")
                return
            except psycopg2.OperationalError as e:
                logger.error(f"Попытка {attempt + 1} подключения к БД не удалась: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(5)
        
    def create_tables(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    registered_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    text TEXT NOT NULL,
                    priority INTEGER NOT NULL CHECK (priority BETWEEN 0 AND 5),
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP NOT NULL,
                    is_completed BOOLEAN DEFAULT FALSE
                )
            """)
            self.conn.commit()
            logger.info("Таблицы созданы/проверены")
    
    
    
    def execute_safe(self, query, params=None):
        df
    
    def fetch_safe(self, query, params=None):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params or ())
                return cur.fetchall()
        except psycopg2.Error as e:
            logger.error(f"Ошибка базы данных: {e}")
            return None
        
        
    def add_user(self,  user_id, username, first_name, last_name):
        df
        
        
    def add_reminder(self, user_id, text, priority, days):
        expires_at = datetime.now() + timedelta(days=days)
        result = self.fetch_safe("""
            INSERT INTO reminders (user_id, text, priority, expires_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (user_id, text, priority, expires_at))
        return result[0][0] if result else None
        
        
    def get_today_reminders(self, user_id):
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        return self.fetch_safe("""
            SELECT id, text, priority
            FROM reminders
            WHERE user_id = %s 
            AND expires_at BETWEEN %s AND %s
            AND is_completed = FALSE
            ORDER BY priority DESC
        """, (user_id, today, tomorrow))
    
    
    def get_all_users(self):
        result = self.fetch_safe("SELECT user_id FROM users")
        return [row[0] for row in result] if result else []
    
    # def delete_reminder()
    
    # def get_deleted_reminders()
    
    # def delete_old_reminders()
    
    
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Соединение с базой данных закрыто")