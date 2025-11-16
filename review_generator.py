"""
综述生成器 - 基于论文总结和主题聚类生成结构化文献综述
"""
from typing import List, Dict
from llm_client import LLMClient
from prompt_template import get_review_generation_prompt


class ReviewGenerator:
    """综述生成器"""
    
    def __init__(self, llm_client: LLMClient, language: str = 'en'):
        self.llm_client = llm_client
        self.language = language
    
    def generate_review(self, summaries: List[str], topics: str, trends: str, query: str, papers: List[Dict]) -> str:
        """生成完整综述
        
        Args:
            summaries: 论文总结列表
            topics: 主题聚类结果
            trends: 趋势分析结果
            query: 用户查询
            papers: 论文列表（包含标题等信息，用于生成参考文献）
        """
        prompt = get_review_generation_prompt(summaries, topics, trends, query, papers, self.language)
        
        # 使用推理模型生成综述
        review = self.llm_client.get_response(prompt=prompt, use_reasoning_model=True)
        
        return review

