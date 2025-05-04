#!/usr/bin/env python
import requests
import smtplib
from email.mime.text import MIMEText
import time
import sys
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройки
SITE_URL = "https://your-domain.com"
EMAIL_FROM = os.environ.get("MONITORING_EMAIL_FROM")
EMAIL_TO = os.environ.get("MONITORING_EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("MONITORING_EMAIL_PASSWORD")
EMAIL_SERVER = os.environ.get("MONITORING_EMAIL_SERVER", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("MONITORING_EMAIL_PORT", "587"))

def check_site():
    """Проверяет доступность сайта"""
    try:
        start_time = time.time()
        response = requests.get(SITE_URL, timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            return True, response_time
        else:
            return False, f"Ошибка статуса: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Ошибка соединения: {str(e)}"

def send_alert_email(message):
    """Отправляет email с предупреждением"""
    try:
        msg = MIMEText(message)
        msg['Subject'] = f"ALERT: Проблема с сайтом {SITE_URL}"
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        
        server = smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {str(e)}")
        return False

def main():
    """Основная функция мониторинга"""
    success, result = check_site()
    
    if success:
        if isinstance(result, float):
            print(f"Сайт доступен. Время ответа: {result:.2f} сек.")
        else:
            print(f"Сайт доступен: {result}")
        sys.exit(0)
    else:
        error_message = f"Сайт {SITE_URL} недоступен. Причина: {result}"
        print(error_message)
        
        if EMAIL_FROM and EMAIL_TO and EMAIL_PASSWORD:
            if send_alert_email(error_message):
                print("Предупреждение отправлено по email.")
            else:
                print("Не удалось отправить предупреждение по email.")
        
        sys.exit(1)

if __name__ == "__main__":
    main()