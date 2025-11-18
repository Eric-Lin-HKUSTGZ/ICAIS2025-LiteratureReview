"""
综述生成器 v4 - 基于v2结构融合v3规范的纯Prompt方案
"""
from llm_client import LLMClient
from prompt_template_v4 import (
    get_query_understanding_prompt,
    get_literature_review_generation_prompt,
)
from config import Config


class ReviewGeneratorV4:
    """综述生成器 v4 - 结合v4模板的两阶段流程"""

    def __init__(self, llm_client: LLMClient, language: str = 'en'):
        self.llm_client = llm_client
        self.language = language
        self.config = Config

    def understand_query(self, query: str) -> str:
        """阶段1：查询理解与知识规划"""
        prompt = get_query_understanding_prompt(query, self.language)

        return self.llm_client.get_response(
            prompt=prompt,
            use_reasoning_model=True,
            timeout=self.config.LLM_REQUEST_TIMEOUT * 3,
        )

    def generate_review(self, query: str, knowledge_plan: str) -> str:
        """阶段2：基于v4模板生成综述"""
        prompt = get_literature_review_generation_prompt(
            query, knowledge_plan, self.language
        )

        return self.llm_client.get_response(
            prompt=prompt,
            use_reasoning_model=True,
            timeout=self.config.LLM_REQUEST_TIMEOUT * 5,
        )

    def generate(self, query: str) -> str:
        """完整管线：查询理解 -> 综述生成"""
        knowledge_plan = self.understand_query(query)
        return self.generate_review(query, knowledge_plan)

