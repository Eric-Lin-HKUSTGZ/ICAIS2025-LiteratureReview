"""
文献分析器 - 负责关键词提取、领域分析、论文分类、论文总结、主题聚类、趋势分析
"""
from typing import List, Dict, Optional
from llm_client import LLMClient
from prompt_template import (
    get_keyword_extraction_prompt,
    get_domain_analysis_prompt,
    get_paper_classification_prompt,
    get_paper_summary_prompt,
    get_topic_clustering_prompt,
    get_trend_analysis_prompt
)
from config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed


class LiteratureAnalyzer:
    """文献分析器"""
    
    def __init__(self, llm_client: LLMClient, language: str = 'en'):
        self.llm_client = llm_client
        self.language = language
        self.config = Config
    
    def extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        prompt = get_keyword_extraction_prompt(query, self.language)
        response = self.llm_client.get_response(prompt=prompt)
        
        # 解析关键词
        keywords = [kw.strip() for kw in response.split(',')]
        keywords = [kw for kw in keywords if kw and len(kw) > 0]
        
        # 限制为3-4个关键词
        return keywords[:4]
    
    def analyze_domain(self, query: str, keywords: List[str]) -> str:
        """分析研究领域"""
        prompt = get_domain_analysis_prompt(query, keywords, self.language)
        domain_analysis = self.llm_client.get_response(prompt=prompt)
        return domain_analysis
    
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
            summary = self.llm_client.get_response(prompt=prompt)
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

