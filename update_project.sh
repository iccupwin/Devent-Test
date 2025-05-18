#!/bin/bash

set -e

PROJECT_DIR="/opt/Devent-Test"
VENV="$PROJECT_DIR/.venv/bin/activate"
SERVICE="devent"
LOG_FILE="/var/log/devent_update.log"
NOW=$(date +"%Y-%m-%d %H:%M:%S")

# === Telegram ===
TG_TOKEN="8121738095:AAHyg7m3nAKJmFKAtVflMYPf1RwFXKnw5mQ"
TG_CHAT_ID="458997990"
TG_URL="https://api.telegram.org/bot$TG_TOKEN/sendMessage"
send_message() {
  curl -s -X POST "$TG_URL" \
    -d chat_id="$TG_CHAT_ID" \
    -d text="$1" \
    -d parse_mode="HTML" > /dev/null
}

{
echo ""
echo "🔄 [$NOW] === ОБНОВЛЕНИЕ НАЧАТО ==="

cd "$PROJECT_DIR"
echo "📦 Перешёл в $PROJECT_DIR"

source "$VENV"
echo "🐍 Активировал виртуальное окружение"

echo "⬇️ Обновление из Git..."
git pull origin main

echo "📦 Установка зависимостей..."
pip install -r requirements.txt

echo "🧱 Применение миграций..."
python manage.py migrate

echo "🎨 Сборка статики..."
python manage.py collectstatic --noinput

echo "🔁 Перезапуск $SERVICE..."
systemctl restart "$SERVICE"

echo "✅ [$NOW] Обновление завершено успешно!"
send_message "✅ <b>Devent обновлён успешно</b>\n<b>Время:</b> $NOW"

} >> "$LOG_FILE" 2>&1 || {
  ERROR_NOW=$(date +"%Y-%m-%d %H:%M:%S")
  echo "❌ [$ERROR_NOW] Обновление завершилось с ошибкой" >> "$LOG_FILE"
  send_message "❌ <b>Ошибка при обновлении Devent!</b>\n<b>Время:</b> $ERROR_NOW"
  exit 1
}
