import anthropic
import asyncio
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS
from shared.memory import add_message, get_project_history, save_artifact


class BaseAgent:
    """Barcha agentlarning asosi"""

    def __init__(self, name: str, emoji: str, system_prompt: str):
        self.name         = name
        self.emoji        = emoji
        self.system_prompt = system_prompt
        self.client       = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    async def think(self, project_id: str, user_message: str,
                    extra_context: str = "") -> str:
        """
        Agentni fikrlash: loyiha tarixi + yangi vazifa → javob
        """
        # Loyiha tarixini olish
        history = await get_project_history(project_id, limit=30)

        # Xabarlar ro'yxatini yasash
        messages = []

        # Avvalgi tarixni qo'shish
        for (agent, role, content) in history:
            if role == "user":
                messages.append({"role": "user", "content": content})
            else:
                messages.append({"role": "assistant", "content": f"[{agent}]: {content}"})

        # Yangi vazifani qo'shish
        full_message = user_message
        if extra_context:
            full_message += f"\n\n📎 Qo'shimcha kontekst:\n{extra_context}"

        messages.append({"role": "user", "content": full_message})

        # Claude API chaqirish
        response = await self.client.messages.create(
            model      = CLAUDE_MODEL,
            max_tokens = MAX_TOKENS,
            system     = self.system_prompt,
            messages   = messages,
        )

        answer = response.content[0].text

        # Tarixga saqlash
        await add_message(project_id, self.name, "user",      user_message)
        await add_message(project_id, self.name, "assistant", answer)

        return answer

    async def think_and_save_code(self, project_id: str, user_message: str,
                                   filename: str, iteration: int = 0,
                                   extra_context: str = "") -> str:
        """Fikrlaydi va kodni saqlaydi"""
        answer = await self.think(project_id, user_message, extra_context)

        # Kodni ajratib olish
        code = self._extract_code(answer)
        if code:
            await save_artifact(
                project_id = project_id,
                agent      = self.name,
                art_type   = "code",
                content    = code,
                filename   = filename,
                iteration  = iteration,
            )

        return answer

    def _extract_code(self, text: str) -> str:
        """```code``` bloklarini ajratib olish"""
        import re
        pattern = r"```(?:\w+)?\n?(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return "\n\n# ===== NEXT FILE =====\n\n".join(matches) if matches else ""

    def header(self) -> str:
        return f"{self.emoji} **{self.name}**"
