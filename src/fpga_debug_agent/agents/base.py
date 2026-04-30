from __future__ import annotations

from abc import ABC, abstractmethod
from fpga_debug_agent.models import AgentResult, RunContext


class Agent(ABC):
    name: str

    @abstractmethod
    def run(self, ctx: RunContext) -> AgentResult:
        raise NotImplementedError
