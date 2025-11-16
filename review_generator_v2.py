"""
综述生成器 v2 - 纯Prompt文献综述生成方案
两阶段生成：查询理解 + 综述生成
"""
from typing import Dict
from llm_client import LLMClient
from prompt_template_v2 import (
    get_query_understanding_prompt,
    get_literature_review_generation_prompt
)
from config import Config


class ReviewGeneratorV2:
    """综述生成器 v2 - 纯Prompt方案"""
    
    def __init__(self, llm_client: LLMClient, language: str = 'en'):
        self.llm_client = llm_client
        self.language = language
        self.config = Config
    
    def understand_query(self, query: str) -> str:
        """阶段1：查询理解与知识规划
        
        Args:
            query: 用户查询
        
        Returns:
            知识规划结果
        """
        prompt = get_query_understanding_prompt(query, self.language)
        
        # 使用推理模型进行深度查询理解
        knowledge_plan = self.llm_client.get_response(
            prompt=prompt,
            use_reasoning_model=True,
            timeout=self.config.LLM_REQUEST_TIMEOUT * 3  # 给更多时间进行深度思考
        )
        
        return knowledge_plan
    
    def generate_review(self, query: str, knowledge_plan: str) -> str:
        """阶段2：生成文献综述
        
        Args:
            query: 用户查询
            knowledge_plan: 知识规划结果
        
        Returns:
            生成的文献综述
        """
        prompt = get_literature_review_generation_prompt(query, knowledge_plan, self.language)
        
        # 使用推理模型生成高质量综述
        review = self.llm_client.get_response(
            prompt=prompt,
            use_reasoning_model=True,
            timeout=self.config.LLM_REQUEST_TIMEOUT * 5  # 给更多时间生成长文本
        )
        
        return review
    
    def generate(self, query: str) -> str:
        """完整生成流程：查询理解 + 综述生成
        
        Args:
            query: 用户查询
        
        Returns:
            生成的文献综述
        """
        # 阶段1：查询理解与知识规划
        knowledge_plan = self.understand_query(query)
        
        # 阶段2：生成文献综述
        review = self.generate_review(query, knowledge_plan)
        
        return review

