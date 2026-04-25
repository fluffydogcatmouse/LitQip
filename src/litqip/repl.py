from __future__ import annotations

import logging

from litqip.agent import AgentLoop, build_system_prompt, load_project_context
from litqip.constants import BANNER
from litqip.compression import auto_compact
from litqip.llm import LLMClient
from litqip.skills import skills
from litqip.todo import todo

logger = logging.getLogger("litqip.repl")

PROMPT = "\033[36mlitqip >> \033[0m"


class REPL:
    def __init__(self) -> None:
        self._history: list[dict] = []
        self._agent: AgentLoop | None = None

    def _init_agent(self) -> AgentLoop:
        if self._agent is None:
            self._agent = AgentLoop(LLMClient.from_env())
        return self._agent

    def _print_response(self, response) -> None:
        """Print assistant text response."""
        text = response.text
        if text:
            print(text)

    def _handle_repl_command(self, line: str) -> bool:
        """
        Handle built-in REPL commands.
        Returns True if the line was a command (consumed), False otherwise.
        """
        cmd = line.strip().lower()
        if cmd in ("/q", "/exit", "/quit"):
            return True
        if not cmd:
            return True  # empty input, just re-prompt
        if cmd == "/compact":
            if self._history:
                agent = self._init_agent()
                self._history[:] = auto_compact(self._history, agent._llm)
                print("Context compressed.")
            return True
        if cmd == "/todo":
            print(todo.render())
            return True
        if cmd.startswith("/todo "):
            content = line.strip()[6:].strip()
            if content:
                todo.add(content)
            print(todo.render())
            return True
        if cmd == "/skills":
            print(skills.descriptions())
            return True
        if cmd == "/clear":
            print("\033[2J\033[H", end="")
            self._history.clear()
            print("History cleared.")
            return True
        if cmd == "/help":
            print(
                "Commands:\n"
                "  /todo [content]  - Show todos, or add a todo\n"
                "  /skills          - List available skills\n"
                "  /compact         - Manually compress context\n"
                "  /clear           - Clear conversation history\n"
                "  /exit            - Exit REPL"
            )
            return True
        return False

    def _initialize_session(self) -> None:
        """Reset conversation state: system prompt + project context."""
        self._history.clear()
        self._history.append({"role": "system", "content": build_system_prompt()})
        ctx = load_project_context()
        if ctx:
            self._history.append({"role": "user", "content": f"Project context:\n{ctx}\n\nAuto-load files marked as '始终加载' using read_file. Do NOT load conditional files yet — they will be loaded on demand when I trigger their condition."})
            agent = self._init_agent()
            self._print_response(agent.run(self._history))
            print()

    def run(self) -> None:
        print(BANNER)
        print("/help for commands. Ctrl-D or /exit to quit.\n")
        self._initialize_session()
        while True:
            try:
                line = input(PROMPT)
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print("\nUse /exit to quit.")
                continue

            if self._handle_repl_command(line):
                if line.strip().lower() in ("/q", "/exit", "/quit"):
                    break
                continue

            self._history.append({"role": "user", "content": line})

            agent = self._init_agent()
            response = agent.run(self._history)

            self._print_response(response)
            print()
