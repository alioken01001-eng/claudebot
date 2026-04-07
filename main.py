"""
🤖 MAIN — Telegram bot ishga tushirish

BUYRUQLAR:
/start          — Botni ishga tushirish
/help           — Yordam
/project <text> — Yangi loyiha boshlash
/chat <agent> <text> — Agent bilan suhbat
/export_<id>    — Loyiha kodlarini yuklab olish
/status         — Joriy holat
"""

import asyncio
import logging
import os
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from config import TELEGRAM_BOT_TOKEN, ADMIN_USER_ID
from orchestrator import Orchestrator
from shared.memory import init_db, get_artifacts

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# HANDLERS
# ──────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Men **Multi-Agent AI Development System** botiman!\n\n"
        "Men 7 ta AI agent yordamida loyihangizni yarataman:\n"
        "🔍 Researcher → 🏗️ Architect → 🎨 Frontend\n"
        "⚙️ Backend → 🖥️ DevOps → ✅ Reviewer → 🧪 Tester\n\n"
        "**Boshlash uchun:**\n"
        "`/project <loyiha tavsifi>`\n\n"
        "**Misol:**\n"
        "`/project E-commerce sayt: foydalanuvchilar mahsulot sotib olishi, "
        "admin panel, to'lov tizimi va real-time bildirishnomalar bo'lsin`\n\n"
        "📖 To'liq yordam: /help",
        parse_mode="Markdown"
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **BUYRUQLAR:**\n\n"
        "`/project <tavsif>` — Yangi loyiha (agentlar to'liq ishlaydi)\n\n"
        "`/chat researcher <savol>` — Researcher bilan suhbat\n"
        "`/chat architect <savol>` — Architect bilan suhbat\n"
        "`/chat frontend <savol>` — Frontend bilan suhbat\n"
        "`/chat backend <savol>` — Backend bilan suhbat\n"
        "`/chat devops <savol>` — DevOps bilan suhbat\n"
        "`/chat reviewer <savol>` — Reviewer bilan suhbat\n"
        "`/chat tester <savol>` — Tester bilan suhbat\n\n"
        "`/export_<id>` — Loyiha kodlarini yuklab olish\n"
        "`/status` — Bot holati\n\n"
        "**Maslahat:** Loyiha tavsifini qanchalik batafsil bersangiz, natija shunchalik yaxshi bo'ladi!",
        parse_mode="Markdown"
    )


async def cmd_project(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Yangi loyiha boshlash"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not ctx.args:
        await update.message.reply_text(
            "❌ Loyiha tavsifini kiriting:\n"
            "`/project <tavsif>`",
            parse_mode="Markdown"
        )
        return

    brief = " ".join(ctx.args)
    if len(brief) < 20:
        await update.message.reply_text(
            "⚠️ Loyiha tavsifini batafsilroq yozing (kamida 20 ta belgi)."
        )
        return

    orch = Orchestrator(ctx.bot)

    # Asinxron ishga tushirish (bloklamaydi)
    asyncio.create_task(
        orch.run_project(chat_id, user_id, brief)
    )


async def cmd_chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Agent bilan alohida suhbat"""
    chat_id = update.effective_chat.id

    if len(ctx.args) < 2:
        await update.message.reply_text(
            "❌ Format: `/chat <agent> <xabar>`\n"
            "Agentlar: researcher, architect, frontend, backend, devops, reviewer, tester",
            parse_mode="Markdown"
        )
        return

    agent_name = ctx.args[0].lower()
    message    = " ".join(ctx.args[1:])

    # Yangi project_id (yoki oxirgi loyiha ishlatilishi mumkin)
    project_id = f"chat_{update.effective_user.id}"

    orch = Orchestrator(ctx.bot)
    await update.message.reply_text(f"🤔 {agent_name} o'ylamoqda...")

    asyncio.create_task(
        orch.chat_with_agent(chat_id, project_id, agent_name, message)
    )


async def cmd_export(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Loyiha kodlarini yuborish"""
    text = update.message.text or ""
    # /export_abc123
    parts = text.split("_")
    if len(parts) < 2:
        await update.message.reply_text("❌ Format: /export_<project_id>")
        return

    project_id = parts[1].strip()
    artifacts  = await get_artifacts(project_id)

    if not artifacts:
        await update.message.reply_text(f"❌ Loyiha topilmadi: `{project_id}`", parse_mode="Markdown")
        return

    await update.message.reply_text(
        f"📦 **Loyiha {project_id}** — {len(artifacts)} ta fayl:\n\n"
        "Fayllar yuklanmoqda...",
        parse_mode="Markdown"
    )

    for (agent, art_type, filename, content, iteration) in artifacts[:10]:
        if content and len(content) > 50:
            preview = content[:3500]
            await update.message.reply_text(
                f"📄 **{filename or agent}** (v{iteration}):\n"
                f"```\n{preview}\n```",
                parse_mode="Markdown"
            )
            await asyncio.sleep(0.5)


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ **Bot ishlayapti!**\n\n"
        "🤖 Agentlar: 7 ta (Researcher, Architect, Frontend, Backend, DevOps, Reviewer, Tester)\n"
        "🧠 Model: claude-opus-4-5\n"
        "🔄 Review iteratsiyalari: 3 ta\n\n"
        "Loyiha boshlash: `/project <tavsif>`",
        parse_mode="Markdown"
    )


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Oddiy xabarlar — orchestrator bilan muloqot"""
    text    = update.message.text or ""
    chat_id = update.effective_chat.id

    if len(text) > 30:
        await update.message.reply_text(
            "💡 Loyiha boshlash uchun: `/project <tavsifingiz>`\n"
            "Agent bilan suhbat: `/chat backend <savolingiz>`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("Salom! /help buyrug'ini ko'ring.")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    # DB ishga tushirish
    asyncio.get_event_loop().run_until_complete(init_db())

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("project", cmd_project))
    app.add_handler(CommandHandler("chat",    cmd_chat))
    app.add_handler(CommandHandler("status",  cmd_status))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^/export_"), cmd_export))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("🤖 Multi-Agent Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
