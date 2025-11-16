"""
文献分析器 - 负责关键词提取、领域分析、论文分类、论文总结、主题聚类、趋势分析
"""
from typing import List, Dict, Optional, Tuple
from llm_client import LLMClient
from prompt_template import (
    get_keyword_extraction_prompt,
    get_domain_analysis_prompt,
    get_paper_classification_prompt,
    get_paper_summary_prompt,
    get_topic_clustering_prompt,
    get_trend_analysis_prompt,
    get_paper_validation_prompt
)
from config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed


class LiteratureAnalyzer:
    """文献分析器"""
    
    def __init__(self, llm_client: LLMClient, language: str = 'en'):
        self.llm_client = llm_client
        self.language = language
        self.config = Config
    
    def extract_keywords(self, query: str, intent_result: dict = None) -> List[str]:
        """提取关键词 - 基于意图分析结果生成更准确的关键词"""
        prompt = get_keyword_extraction_prompt(query, intent_result, self.language)
        response = self.llm_client.get_response(prompt=prompt)
        
        # 解析关键词
        keywords = [kw.strip() for kw in response.split(',')]
        keywords = [kw for kw in keywords if kw and len(kw) > 0]
        
        # 限制为3-4个关键词
        return keywords[:4]
    
    def analyze_domain(self, query: str, keywords: List[str], intent_result: dict = None) -> str:
        """分析研究领域 - 增强版，要求输出技术全称、相关领域、关键概念、可能的歧义澄清"""
        prompt = get_domain_analysis_prompt(query, keywords, intent_result, self.language)
        # 使用推理模型进行高质量的领域分析
        domain_analysis = self.llm_client.get_response(
            prompt=prompt,
            use_reasoning_model=True,
            timeout=self.config.DOMAIN_ANALYSIS_TIMEOUT * 2
        )
        return domain_analysis
    
    def validate_retrieved_papers(self, papers: List[Dict], query: str, intent_result: dict) -> Tuple[List[Dict], bool]:
        """验证检索到的论文是否与查询意图匹配
        
        Args:
            papers: 检索到的论文列表
            query: 用户查询
            intent_result: 查询意图分析结果
        
        Returns:
            (validated_papers, need_reretrieval): 验证后的论文列表和是否需要重新检索
        """
        if not papers:
            return [], False
        
        try:
            prompt = get_paper_validation_prompt(papers, query, intent_result, self.language)
            # 使用推理模型进行验证
            validation_result = self.llm_client.get_response(
                prompt=prompt,
                use_reasoning_model=True,
                timeout=self.config.PAPER_CLASSIFICATION_TIMEOUT * 2
            )
            
            # 解析验证结果，判断是否需要重新检索
            need_reretrieval = self._parse_validation_result(validation_result)
            
            # 如果不需要重新检索，返回原论文列表
            # 如果需要重新检索，也返回原列表（由调用方决定是否重新检索）
            return papers, need_reretrieval
        except Exception as e:
            # 如果验证失败，默认不重新检索
            print(f"⚠️  论文验证失败: {e}，继续使用原论文列表")
            return papers, False
    
    def _parse_validation_result(self, validation_result: str) -> bool:
        """解析验证结果，判断是否需要重新检索"""
        # 检查验证结果中是否包含"需要重新检索"、"re-retrieval"等关键词
        validation_lower = validation_result.lower()
        
        # 中文关键词
        if "需要重新检索" in validation_result or "需要调整" in validation_result or "不匹配" in validation_result:
            # 进一步检查是否大部分论文不匹配
            if "超过50%" in validation_result or "大部分" in validation_result or "多数" in validation_result:
                return True
        
        # 英文关键词
        if "re-retrieval" in validation_lower or "re-retrieve" in validation_lower or "adjust" in validation_lower:
            if "more than 50%" in validation_lower or "most" in validation_lower or "majority" in validation_lower:
                return True
        
        return False
    
    def classify_papers(self, papers: List[Dict], query: str) -> List[Dict]:
        """论文分类与筛选"""
        if not papers:
            return []
        
        # 如果论文数量较少，直接返回，不需要分类
        if len(papers) <= 15:
            return papers
        
        # 尝试使用LLM进行分类，如果超时则使用fallback
        try:
            # 限制论文数量，避免prompt过长导致超时
            papers_to_classify = papers[:20]  # 最多处理20篇
            prompt = get_paper_classification_prompt(papers_to_classify, query, self.language)
            # 不使用推理模型，使用普通模型以加快速度，并增加超时时间
            classification_result = self.llm_client.get_response(
                prompt=prompt, 
                use_reasoning_model=False,
                timeout=self.config.PAPER_CLASSIFICATION_TIMEOUT * 2  # 使用配置的超时时间（翻倍）
            )
            # 由于分类结果可能比较复杂，这里简化处理：直接返回前15篇论文
            # 实际应用中可以根据LLM返回的分类结果进行筛选
            return papers[:min(len(papers), 15)]
        except Exception as e:
            # 如果分类失败（超时或其他错误），使用fallback：直接返回前15篇论文
            print(f"⚠️  论文分类失败: {e}，使用fallback方法：返回前15篇论文")
            return papers[:min(len(papers), 15)]
    
    def summarize_papers(self, papers: List[Dict], query: str) -> List[str]:
        """论文内容总结"""
        if not papers:
            return []
        
        summaries = []
        
        # 使用线程池并行处理论文总结
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for paper in papers:
                future = executor.submit(self._summarize_single_paper, paper, query)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    summary = future.result()
                    if summary:
                        summaries.append(summary)
                except Exception as e:
                    print(f"⚠️  论文总结失败: {e}")
                    continue
        
        return summaries
    
    def _summarize_single_paper(self, paper: Dict, query: str) -> Optional[str]:
        """总结单篇论文"""
        try:
            prompt = get_paper_summary_prompt(paper, query, self.language)
            # 使用推理模型进行高质量的论文总结
            summary = self.llm_client.get_response(
                prompt=prompt,
                use_reasoning_model=True,
                timeout=self.config.PAPER_SUMMARY_TIMEOUT
            )
            return summary
        except Exception as e:
            print(f"⚠️  单篇论文总结失败: {e}")
            return None
    
    def cluster_topics(self, summaries: List[str]) -> str:
        """主题聚类"""
        if not summaries:
            return ""
        
        try:
            prompt = get_topic_clustering_prompt(summaries, self.language)
            clustering_result = self.llm_client.get_response(
                prompt=prompt, 
                use_reasoning_model=True,
                timeout=self.config.TOPIC_CLUSTERING_TIMEOUT * 2  # 增加超时时间
            )
            return clustering_result
        except Exception as e:
            # 如果聚类失败，返回空字符串，不影响后续流程
            print(f"⚠️  主题聚类失败: {e}，跳过此步骤")
            return ""
    
    def analyze_trends(self, papers: List[Dict]) -> str:
        """趋势分析"""
        if not papers:
            return ""
        
        try:
            prompt = get_trend_analysis_prompt(papers, self.language)
            trend_analysis = self.llm_client.get_response(
                prompt=prompt, 
                use_reasoning_model=True,
                timeout=self.config.TREND_ANALYSIS_TIMEOUT * 2  # 增加超时时间
            )
            return trend_analysis
        except Exception as e:
            # 如果趋势分析失败，返回空字符串，不影响后续流程
            print(f"⚠️  趋势分析失败: {e}，跳过此步骤")
            return ""

