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
    
    
    
    def execute_safe()
    
    def fetch_safe()
    
    def add_user()
    
    def add_reminder()
    
    def get_today_reminders()
    
    def get_all_users()
    
    # def delete_reminder()
    
    # def get_deleted_reminders()
    
    # def delete_old_reminders()
    
    
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Соединение с базой данных закрыто")