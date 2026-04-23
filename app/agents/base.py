from __future__ import annotations

import logging
from dataclasses import dataclass


@dataclass
class AgentContext:
    pipeline_id: str


class BaseAgent:
    name = "base"

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)

