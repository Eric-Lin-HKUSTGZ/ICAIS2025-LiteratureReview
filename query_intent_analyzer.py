"""
查询意图分析器 - 深度分析查询意图，消除歧义
"""
from typing import Dict
from llm_client import LLMClient
from prompt_template import get_query_intent_analysis_prompt
from config import Config


class QueryIntentAnalyzer:
    """查询意图分析器"""
    
    def __init__(self, llm_client: LLMClient, language: str = 'en'):
        self.llm_client = llm_client
        self.language = language
        self.config = Config
    
    def analyze_intent(self, query: str) -> Dict[str, str]:
        """深度分析查询意图，消除歧义
        
        Args:
            query: 用户查询
        
        Returns:
            意图分析结果字典，包含：
            - full_name: 技术全称
            - domain: 研究领域
            - key_concepts: 关键概念
            - disambiguation: 歧义澄清
            - recommended_keywords: 推荐的关键词（避免歧义）
        """
        prompt = get_query_intent_analysis_prompt(query, self.language)
        
        # 使用推理模型进行深度意图分析
        response = self.llm_client.get_response(
            prompt=prompt,
            use_reasoning_model=True,
            timeout=self.config.DOMAIN_ANALYSIS_TIMEOUT * 2
        )
        
        # 解析响应，提取结构化信息
        intent_result = self._parse_intent_response(response)
        
        return intent_result
    
    def _parse_intent_response(self, response: str) -> Dict[str, str]:
        """解析意图分析响应，提取结构化信息"""
        intent_result = {
            "raw_response": response,
            "full_name": "",
            "domain": "",
            "key_concepts": "",
            "disambiguation": "",
            "recommended_keywords": []
        }
        
        # 尝试提取各个字段
        lines = response.split('\n')
        current_field = None
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # 检查是否是字段标题
            if '技术全称' in line_stripped or 'Full Name' in line_stripped or '全称' in line_stripped:
                if current_field:
                    intent_result[current_field] = "\n".join(current_content).strip()
                current_field = "full_name"
                current_content = []
                parts = line_stripped.split(':', 1)
                if len(parts) > 1:
                    current_content.append(parts[1].strip())
            elif '研究领域' in line_stripped or 'Domain' in line_stripped or '领域' in line_stripped:
                if current_field:
                    intent_result[current_field] = "\n".join(current_content).strip()
                current_field = "domain"
                current_content = []
                parts = line_stripped.split(':', 1)
                if len(parts) > 1:
                    current_content.append(parts[1].strip())
            elif '关键概念' in line_stripped or 'Key Concepts' in line_stripped or '概念' in line_stripped:
                if current_field:
                    intent_result[current_field] = "\n".join(current_content).strip()
                current_field = "key_concepts"
                current_content = []
                parts = line_stripped.split(':', 1)
                if len(parts) > 1:
                    current_content.append(parts[1].strip())
            elif '歧义' in line_stripped or 'Disambiguation' in line_stripped or '澄清' in line_stripped:
                if current_field:
                    intent_result[current_field] = "\n".join(current_content).strip()
                current_field = "disambiguation"
                current_content = []
                parts = line_stripped.split(':', 1)
                if len(parts) > 1:
                    current_content.append(parts[1].strip())
            elif '推荐关键词' in line_stripped or 'Recommended Keywords' in line_stripped or '关键词' in line_stripped:
                if current_field:
                    intent_result[current_field] = "\n".join(current_content).strip()
                current_field = "recommended_keywords"
                current_content = []
                parts = line_stripped.split(':', 1)
                if len(parts) > 1:
                    current_content.append(parts[1].strip())
            elif current_field:
                current_content.append(line_stripped)
        
        # 保存最后一个字段
        if current_field:
            intent_result[current_field] = "\n".join(current_content).strip()
        
        # 解析推荐关键词列表
        if intent_result.get("recommended_keywords"):
            keywords_text = intent_result["recommended_keywords"]
            # 尝试按逗号分割
            keywords = [kw.strip() for kw in keywords_text.split(',')]
            keywords = [kw for kw in keywords if kw]
            intent_result["recommended_keywords"] = keywords[:5]  # 最多5个关键词
        
        return intent_result

