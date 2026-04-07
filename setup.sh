#!/bin/bash
# ============================================
#  MULTI-AGENT BOT — O'RNATISH VA ISHGA TUSHIRISH
# ============================================

echo "🤖 Multi-Agent Bot o'rnatilmoqda..."

# 1. Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Kerakli kutubxonalar
pip install -r requirements.txt

# 3. .env faylini tayyorlash
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  .env faylini to'ldiring:"
    echo "   TELEGRAM_BOT_TOKEN  — @BotFather dan"
    echo "   ANTHROPIC_API_KEY   — console.anthropic.com dan"
    echo "   TAVILY_API_KEY      — tavily.com dan (BEPUL)"
    echo "   ADMIN_USER_ID       — @userinfobot ga /start yuboring"
    echo ""
fi

echo "✅ O'rnatish tugadi!"
echo ""
echo "Boshlash uchun:"
echo "  1. nano .env  (API kalitlarni kiriting)"
echo "  2. python main.py"
