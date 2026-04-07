import os
from dotenv import load_dotenv

load_dotenv()

# === API KEYS ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY")
TAVILY_API_KEY     = os.getenv("TAVILY_API_KEY")
ADMIN_USER_ID      = int(os.getenv("ADMIN_USER_ID", "0"))

# === MODEL ===
CLAUDE_MODEL   = os.getenv("CLAUDE_MODEL", "claude-opus-4-5")
MAX_TOKENS     = 8000
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))

# === AGENT NAMES ===
AGENTS = {
    "orchestrator" : "🎯 Orchestrator",
    "researcher"   : "🔍 Researcher",
    "architect"    : "🏗️  Architect",
    "frontend"     : "🎨 Frontend",
    "backend"      : "⚙️  Backend",
    "devops"       : "🖥️  DevOps",
    "reviewer"     : "✅ Reviewer",
    "tester"       : "🧪 Tester",
}

# === STATUS KEYWORDS (agentlar shu so'zlarni ishlatadi) ===
STATUS = {
    "DONE"     : "[DONE]",        # Vazifa tugadi
    "FIX"      : "[FIX]",         # Tuzatish kerak
    "APPROVED" : "[APPROVED]",    # Tasdiqlandi
    "BLOCKED"  : "[BLOCKED]",     # To'siq bor, yordam kerak
    "RESEARCH" : "[RESEARCH]",    # Ko'proq ma'lumot kerak
    "DEPLOY"   : "[DEPLOY]",      # Deploy qilishga tayyor
}
