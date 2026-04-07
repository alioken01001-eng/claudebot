"""
🎯 ORCHESTRATOR — Barcha agentlarni boshqaradi

Ishlash tartibi:
1. User loyiha beradi
2. Researcher → eng yaxshi texnologiyalarni topadi
3. Architect  → arxitektura loyihalaydi
4. Frontend + Backend + DevOps → parallel ishlaydi
5. Reviewer → hamma kodni tekshiradi
6. Tester → testlar yozadi
7. Agar [FIX] bo'lsa → tegishli agent qayta ishlaydi (max N marta)
8. [APPROVED] bo'lganda — loyiha tayyor!
"""

import asyncio
import uuid
from telegram import Bot, Message
from config import MAX_ITERATIONS, STATUS, AGENTS
from agents.agents import (
    ResearcherAgent, ArchitectAgent, FrontendAgent,
    BackendAgent, DevOpsAgent, ReviewerAgent, TesterAgent
)
from shared.memory import (
    create_project, update_project_context,
    get_project_context, get_artifacts, save_artifact
)


class Orchestrator:
    def __init__(self, bot: Bot):
        self.bot       = bot
        self.researcher = ResearcherAgent()
        self.architect  = ArchitectAgent()
        self.frontend   = FrontendAgent()
        self.backend    = BackendAgent()
        self.devops     = DevOpsAgent()
        self.reviewer   = ReviewerAgent()
        self.tester     = TesterAgent()

    # ──────────────────────────────────────────
    # ASOSIY FUNKSIYA
    # ──────────────────────────────────────────
    async def run_project(self, chat_id: int, user_id: int, project_brief: str) -> str:
        """Loyihani boshidan oxirigacha boshqaradi"""

        project_id = str(uuid.uuid4())[:8]
        await create_project(project_id, user_id, chat_id, project_brief[:100])

        await self._send(chat_id,
            f"🚀 **Yangi loyiha boshlandi!**\n"
            f"🆔 ID: `{project_id}`\n"
            f"📋 Loyiha: {project_brief[:200]}\n\n"
            f"Agentlar guruhiga yig'ilmoqda... 🤖🤖🤖"
        )

        # ── 1. RESEARCH ──
        await self._send(chat_id, "━"*30 + "\n🔍 **Researcher** ishga tushdi...")
        research = await self._run_agent(
            self.researcher, project_id, chat_id,
            f"Ushbu loyiha uchun eng yaxshi texnologiyalarni tavsiya qil:\n\n{project_brief}"
        )
        await update_project_context(project_id, "research", research[:2000])

        # ── 2. ARCHITECTURE ──
        await self._send(chat_id, "━"*30 + "\n🏗️ **Architect** arxitektura loyihalaydi...")
        research_ctx = await get_project_context(project_id)
        arch = await self._run_agent(
            self.architect, project_id, chat_id,
            f"Quyidagi loyiha va tadqiqot asosida to'liq arxitektura loyihala:\n\n"
            f"LOYIHA: {project_brief}\n\n"
            f"TADQIQOT: {research_ctx.get('research', '')}",
        )
        await update_project_context(project_id, "architecture", arch[:2000])

        # ── 3. PARALLEL: Frontend + Backend + DevOps ──
        await self._send(chat_id,
            "━"*30 + "\n"
            "⚡ **Parallel ishlab ketilmoqda...**\n"
            "  🎨 Frontend\n  ⚙️ Backend\n  🖥️ DevOps"
        )
        ctx = await get_project_context(project_id)
        base_ctx = f"LOYIHA: {project_brief}\n\nARXITEKTURA:\n{ctx.get('architecture','')}"

        fe_task  = self._run_agent(self.frontend, project_id, chat_id,
            f"Arxitekturaga asosan to'liq frontend kodini yoz:\n\n{base_ctx}", save_code=True)
        be_task  = self._run_agent(self.backend, project_id, chat_id,
            f"Arxitekturaga asosan to'liq backend kodini yoz:\n\n{base_ctx}", save_code=True)
        dvo_task = self._run_agent(self.devops, project_id, chat_id,
            f"Arxitekturaga asosan Docker, CI/CD, Nginx konfiguratsiyalarini yoz:\n\n{base_ctx}", save_code=True)

        fe_result, be_result, dv_result = await asyncio.gather(fe_task, be_task, dvo_task)
        await update_project_context(project_id, "frontend_v1", fe_result[:1500])
        await update_project_context(project_id, "backend_v1",  be_result[:1500])
        await update_project_context(project_id, "devops_v1",   dv_result[:1500])

        # ── 4. ITERATIVE REVIEW LOOP ──
        await self._send(chat_id, "━"*30 + "\n✅ **Reviewer** kod sifatini tekshirmoqda...")

        ctx = await get_project_context(project_id)
        all_code = (
            f"=== FRONTEND ===\n{ctx.get('frontend_v1','')}\n\n"
            f"=== BACKEND ===\n{ctx.get('backend_v1','')}\n\n"
            f"=== DEVOPS ===\n{ctx.get('devops_v1','')}"
        )

        iteration = 0
        approved  = False

        while iteration < MAX_ITERATIONS and not approved:
            iteration += 1
            await self._send(chat_id, f"🔄 **Review #{iteration}** boshlandi...")

            review = await self._run_agent(
                self.reviewer, project_id, chat_id,
                f"Quyidagi kodni BATAFSIL tekshir:\n\n{all_code}"
            )
            await update_project_context(project_id, f"review_{iteration}", review[:2000])

            if STATUS["APPROVED"] in review:
                approved = True
                await self._send(chat_id, f"✅ Kod **{iteration}-reviewda TASDIQLANDI!** 🎉")
                break

            # FIX kerak — qaysi agent?
            if STATUS["FIX"] in review:
                await self._send(chat_id, f"🔧 Muammolar topildi! Agentlar to'g'irlandi...")

                # Parallel fix
                fix_ctx = f"REVIEWER TOPGAN MUAMMOLAR:\n{review}\n\nASL KOD:\n{all_code}"

                fe_fix, be_fix, dv_fix = await asyncio.gather(
                    self._run_agent(self.frontend, project_id, chat_id,
                        f"Reviewerning tanqidlarini to'g'irla:\n{fix_ctx}", save_code=True),
                    self._run_agent(self.backend, project_id, chat_id,
                        f"Reviewerning tanqidlarini to'g'irla:\n{fix_ctx}", save_code=True),
                    self._run_agent(self.devops, project_id, chat_id,
                        f"Reviewerning tanqidlarini to'g'irla:\n{fix_ctx}", save_code=True),
                )
                ctx = await get_project_context(project_id)
                all_code = (
                    f"=== FRONTEND v{iteration+1} ===\n{fe_fix[:1000]}\n\n"
                    f"=== BACKEND v{iteration+1} ===\n{be_fix[:1000]}\n\n"
                    f"=== DEVOPS v{iteration+1} ===\n{dv_fix[:1000]}"
                )

        if not approved:
            await self._send(chat_id,
                f"⚠️ {MAX_ITERATIONS} ta review tugadi. Eng yaxshi versiya olingan.\n"
                f"Manual tekshiruv tavsiya etiladi."
            )

        # ── 5. TESTING ──
        await self._send(chat_id, "━"*30 + "\n🧪 **Tester** testlar yozmoqda...")
        ctx = await get_project_context(project_id)
        tests = await self._run_agent(
            self.tester, project_id, chat_id,
            f"Quyidagi kod uchun to'liq test suite yoz:\n\n"
            f"BACKEND: {ctx.get('backend_v1','')[:1000]}\n"
            f"FRONTEND: {ctx.get('frontend_v1','')[:1000]}"
        )

        # ── 6. YAKUN ──
        artifacts = await get_artifacts(project_id)
        await self._send(chat_id,
            "━"*30 + "\n"
            f"🏁 **LOYIHA TUGADI!**\n\n"
            f"📦 Yaratilgan fayllar: {len(artifacts)} ta\n"
            f"🔄 Review iteratsiyalari: {iteration}\n"
            f"✅ Status: {'TASDIQLANDI ✅' if approved else 'QISMAN TAYYOR ⚠️'}\n\n"
            f"Kodlarni olish uchun: /export_{project_id}"
        )

        return project_id

    # ──────────────────────────────────────────
    # YORDAMCHI FUNKSIYALAR
    # ──────────────────────────────────────────
    async def _run_agent(self, agent, project_id: str, chat_id: int,
                          prompt: str, save_code: bool = False) -> str:
        try:
            if save_code:
                result = await agent.think_and_save_code(
                    project_id, prompt,
                    filename  = f"{agent.name.lower()}_output",
                    iteration = 1,
                )
            else:
                result = await agent.think(project_id, prompt)

            # Telegram'ga qisqa xabar yuborish
            preview = result[:800] + ("..." if len(result) > 800 else "")
            await self._send(chat_id,
                f"{agent.emoji} **{agent.name}** javob berdi:\n\n{preview}"
            )
            return result

        except Exception as e:
            err_msg = f"❌ {agent.name} xatosi: {str(e)}"
            await self._send(chat_id, err_msg)
            return f"[ERROR] {str(e)}"

    async def _send(self, chat_id: int, text: str):
        """Telegram'ga xabar yuborish (uzun xabarlarni kesish)"""
        chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
        for chunk in chunks:
            try:
                await self.bot.send_message(
                    chat_id    = chat_id,
                    text       = chunk,
                    parse_mode = "Markdown"
                )
                await asyncio.sleep(0.3)  # Telegram rate limit
            except Exception:
                try:
                    await self.bot.send_message(chat_id=chat_id, text=chunk)
                except Exception as e:
                    print(f"Send error: {e}")

    # ──────────────────────────────────────────
    # AGENTLAR BILAN CHAT (suhbat rejimi)
    # ──────────────────────────────────────────
    async def chat_with_agent(self, chat_id: int, project_id: str,
                               agent_name: str, message: str) -> str:
        """Bitta agent bilan alohida suhbat"""
        agents_map = {
            "researcher": self.researcher,
            "architect":  self.architect,
            "frontend":   self.frontend,
            "backend":    self.backend,
            "devops":     self.devops,
            "reviewer":   self.reviewer,
            "tester":     self.tester,
        }
        agent = agents_map.get(agent_name.lower())
        if not agent:
            return f"❌ Agent topilmadi: {agent_name}"

        result = await agent.think(project_id, message)
        await self._send(chat_id,
            f"{agent.emoji} **{agent.name}** (chat rejimi):\n\n{result[:3000]}"
        )
        return result
