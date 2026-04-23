from __future__ import annotations

from dataclasses import dataclass

from app.agents.base import AgentContext, BaseAgent
from app.utils.llm_client import OpenAILLMClient
from app.utils.json_parser import safe_json_parse


@dataclass
class DiscoveredQueryItem:
    query_text: str


class QueryDiscoveryAgent(BaseAgent):
    name = "query_discovery"

    def __init__(self, llm: OpenAILLMClient | None = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or OpenAILLMClient()

    def run(self, ctx: AgentContext, *, domain: str, industry: str | None, competitors: list[str]) -> list[DiscoveredQueryItem]:
        system = (
            "You are an SEO and AI-search expert.\n"
            "Generate realistic, commercially relevant questions users ask AI assistants.\n"
            "Return ONLY valid JSON matching this schema:\n"
            '{ "queries": [ { "query_text": "string" } ] }\n'
            "Constraints:\n"
            "- 10 to 20 queries\n"
            "- Natural language questions\n"
            "- Include comparison/best-of style queries\n"
            "- Do not include markdown or extra keys\n"
        )
        user = (
            f"Business domain: {domain}\n"
            f"Industry: {industry or ''}\n"
            f"Competitors: {', '.join(competitors) if competitors else ''}\n"
            "Generate queries now."
        )

        parsed, res = self.llm.chat_json(system=system, user=user)
        self.logger.info("[%s] %s completed (tokens=%s)", ctx.pipeline_id, self.name, res.tokens_used)

        queries_obj = parsed if isinstance(parsed, dict) else safe_json_parse(res.text)
        items = []
        if isinstance(queries_obj, dict) and isinstance(queries_obj.get("queries"), list):
            for it in queries_obj["queries"]:
                if isinstance(it, dict) and isinstance(it.get("query_text"), str) and it["query_text"].strip():
                    items.append(DiscoveredQueryItem(query_text=it["query_text"].strip()))

        # deterministic fallback if LLM output is unusable
        if not items:
            fallback = [
                f"What is the best {industry or 'software'} for {domain} alternatives?",
                f"{domain} vs {competitors[0]}" if competitors else f"{domain} competitors comparison",
                f"How does {domain} compare to other {industry or 'tools'}?",
                f"Best {industry or 'tools'} for teams in 2026",
                f"Is {domain} worth it?",
                f"Pricing and features of {domain}",
                f"Top alternatives to {domain}",
                f"How to choose the best {industry or 'tool'}",
                f"Best AI tools for {industry or 'this category'}",
                f"Which {industry or 'platform'} is easiest to use?",
            ]
            items = [DiscoveredQueryItem(query_text=q) for q in fallback[:10]]

        return items

