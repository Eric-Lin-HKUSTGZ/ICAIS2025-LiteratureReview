import requests
import time
import numpy as np
from typing import List, Dict, Optional
from config import Config
from embedding_client import EmbeddingClient


class PaperRetriever:
    """论文检索器 - 基于Semantic Scholar API，失败时fallback到OpenAlex"""

    def __init__(self):
        self.config = Config
        self.embedding_client = None
        self._init_embedding_client()
        # OpenAlex API headers
        self.openalex_headers = {
            'User-Agent': 'ICAIS2025-LiteratureReview/1.0 ( https://github.com/your-repo )'
        }

    def _init_embedding_client(self):
        """初始化embedding客户端"""
        try:
            self.embedding_client = EmbeddingClient()
        except Exception as e:
            print(f"⚠️  Embedding客户端初始化失败: {e}，将跳过语义重排序")
            self.embedding_client = None

    def _convert_openalex_to_semanticscholar_format(self, openalex_work: Dict) -> Dict:
        """将OpenAlex的work格式转换为Semantic Scholar格式"""
        title = openalex_work.get('title', '') or ''
        
        abstract = ''
        if 'abstract_inverted_index' in openalex_work and openalex_work['abstract_inverted_index']:
            try:
                inverted_index = openalex_work['abstract_inverted_index']
                pos_to_word = {}
                for word, positions in inverted_index.items():
                    for pos in positions:
                        pos_to_word[pos] = word
                if pos_to_word:
                    sorted_positions = sorted(pos_to_word.keys())
                    abstract = ' '.join([pos_to_word[pos] for pos in sorted_positions])
            except Exception as e:
                print(f"⚠️  转换 OpenAlex 摘要失败: {e}")
                abstract = ''
        elif 'abstract' in openalex_work and isinstance(openalex_work['abstract'], str):
            abstract = openalex_work['abstract']
        if not abstract:
            abstract = ''
        
        paper_id = openalex_work.get('id', '')
        if paper_id and isinstance(paper_id, str) and paper_id.startswith('https://openalex.org/'):
            paper_id = paper_id.replace('https://openalex.org/', '')
        elif not paper_id:
            paper_id = title
        
        return {
            'paperId': paper_id,
            'title': title,
            'abstract': abstract
        }

    def _get_papers_from_openalex(self, query: str, sort: str, max_results: int, timeout: int = 30) -> List[Dict]:
        """从OpenAlex获取论文（内部方法）"""
        url = "https://api.openalex.org/works"
        
        cleaned_query = query.replace('"', '').replace(' | ', ' ').strip()
        import re
        cleaned_query = re.sub(r'\s+', ' ', cleaned_query).strip()
        
        params = {
            "search": cleaned_query,
            "sort": sort,
            "per_page": min(max_results, 200)
        }
        
        try:
            response = requests.get(
                url, 
                params=params, 
                headers=self.openalex_headers,
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if 'results' in data and data['results']:
                papers = []
                for work in data['results'][:max_results]:
                    paper = self._convert_openalex_to_semanticscholar_format(work)
                    if paper.get('title', '').strip():
                        papers.append(paper)
                return papers
            return []
        except Exception as e:
            print(f"⚠️  OpenAlex检索失败: {e}")
            return []

    def get_newest_paper_openalex(self, query: str, max_results: Optional[int] = None) -> List[Dict]:
        """使用OpenAlex获取最新论文"""
        max_results = max_results or self.config.MAX_PAPERS_PER_QUERY
        return self._get_papers_from_openalex(query, "publication_date:desc", max_results)

    def get_highly_cited_paper_openalex(self, query: str, max_results: Optional[int] = None) -> List[Dict]:
        """使用OpenAlex获取高引用论文"""
        max_results = max_results or self.config.MAX_PAPERS_PER_QUERY
        return self._get_papers_from_openalex(query, "cited_by_count:desc", max_results)

    def get_relevant_paper_openalex(self, query: str, max_results: Optional[int] = None) -> List[Dict]:
        """使用OpenAlex获取相关论文"""
        max_results = max_results or self.config.MAX_PAPERS_PER_QUERY
        return self._get_papers_from_openalex(query, "cited_by_count:desc", max_results)

    def get_newest_paper(self, query: str, max_results: Optional[int] = None, max_retries: Optional[int] = None) -> List[Dict]:
        """获取最新论文（Semantic Scholar失败时fallback到OpenAlex）"""
        max_results = max_results or self.config.MAX_PAPERS_PER_QUERY
        max_retries = min(max_retries or 2, 2)

        url = "http://api.semanticscholar.org/graph/v1/paper/search/bulk"
        params = {"query": query, "fields": "title,abstract,paperId", "sort": "publicationDate:desc"}

        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=self.config.SEMANTIC_SCHOLAR_TIMEOUT)
                
                if response.status_code == 429:
                    return self.get_newest_paper_openalex(query, max_results)
                
                if response.status_code != 200:
                    if attempt < max_retries - 1:
                        time.sleep(min(2 ** attempt, 2))
                        continue
                    else:
                        return self.get_newest_paper_openalex(query, max_results)
                
                data = response.json()
                if 'data' in data:
                    papers = data['data'][:max_results] if data['data'] else []
                    if papers:
                        return papers
                    if attempt < max_retries - 1:
                        time.sleep(min(2 ** attempt, 2))
                    continue
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 2))
                    continue
                else:
                    return self.get_newest_paper_openalex(query, max_results)
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 2))
                    continue
                else:
                    return self.get_newest_paper_openalex(query, max_results)

        return self.get_newest_paper_openalex(query, max_results)

    def get_highly_cited_paper(self, query: str, max_results: Optional[int] = None, max_retries: Optional[int] = None) -> List[Dict]:
        """获取高引用论文（Semantic Scholar失败时fallback到OpenAlex）"""
        max_results = max_results or self.config.MAX_PAPERS_PER_QUERY
        max_retries = min(max_retries or 2, 2)

        url = "http://api.semanticscholar.org/graph/v1/paper/search/bulk"
        params = {"query": query, "fields": "title,abstract,paperId", "sort": "citationCount:desc"}

        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=self.config.SEMANTIC_SCHOLAR_TIMEOUT)
                
                if response.status_code == 429:
                    return self.get_highly_cited_paper_openalex(query, max_results)
                
                if response.status_code != 200:
                    if attempt < max_retries - 1:
                        time.sleep(min(2 ** attempt, 2))
                        continue
                    else:
                        return self.get_highly_cited_paper_openalex(query, max_results)
                
                data = response.json()
                if 'data' in data:
                    papers = data['data'][:max_results] if data['data'] else []
                    if papers:
                        return papers
                    if attempt < max_retries - 1:
                        time.sleep(min(2 ** attempt, 2))
                    continue
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 2))
                    continue
                else:
                    return self.get_highly_cited_paper_openalex(query, max_results)
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 2))
                    continue
                else:
                    return self.get_highly_cited_paper_openalex(query, max_results)

        return self.get_highly_cited_paper_openalex(query, max_results)

    def get_relevant_paper(self, query: str, max_results: Optional[int] = None, max_retries: Optional[int] = None) -> List[Dict]:
        """获取相关论文（Semantic Scholar失败时fallback到OpenAlex）"""
        max_results = max_results or self.config.MAX_PAPERS_PER_QUERY
        max_retries = min(max_retries or 2, 2)

        url = "http://api.semanticscholar.org/graph/v1/paper/search"
        params = {"query": query, "fields": "title,abstract,paperId"}

        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=self.config.SEMANTIC_SCHOLAR_TIMEOUT)
                
                if response.status_code == 429:
                    return self.get_relevant_paper_openalex(query, max_results)
                
                if response.status_code != 200:
                    if attempt < max_retries - 1:
                        time.sleep(min(2 ** attempt, 2))
                        continue
                    else:
                        return self.get_relevant_paper_openalex(query, max_results)
                
                try:
                    data = response.json()
                except ValueError:
                    if attempt < max_retries - 1:
                        time.sleep(min(2 ** attempt, 2))
                        continue
                    else:
                        return self.get_relevant_paper_openalex(query, max_results)

                if 'data' in data:
                    papers = data['data'][:max_results] if data['data'] else []
                    if papers:
                        return papers
                    if attempt < max_retries - 1:
                        time.sleep(min(2 ** attempt, 2))
                    continue
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 2))
                    continue
                else:
                    return self.get_relevant_paper_openalex(query, max_results)
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 2))
                    continue
                else:
                    return self.get_relevant_paper_openalex(query, max_results)

        return self.get_relevant_paper_openalex(query, max_results)

    def merge_and_deduplicate(self, results: Dict[str, List[Dict]]) -> List[Dict]:
        """融合和去重论文"""
        seen_ids = set()
        all_papers = []

        for paper_list in results.values():
            for paper in paper_list:
                paper_id = paper.get('paperId') or paper.get('title', '')
                if paper_id and paper_id not in seen_ids:
                    seen_ids.add(paper_id)
                    all_papers.append(paper)

        return all_papers

    def rerank_by_similarity(self, papers: List[Dict], background_embedding: np.ndarray, background_text: str) -> List[Dict]:
        """基于语义相似度重排序论文"""
        if not self.embedding_client or len(papers) == 0:
            return papers

        try:
            paper_texts = []
            for paper in papers:
                abstract = paper.get('abstract', '') or ''
                title = paper.get('title', '') or ''
                text = f"{title} {abstract}".strip()
                paper_texts.append(text if text else " ")

            paper_embeddings = self.embedding_client.encode(paper_texts, show_progress_bar=False)
            
            if paper_embeddings.ndim == 1:
                paper_embeddings = paper_embeddings.reshape(1, -1)

            similarities = []
            for paper_emb in paper_embeddings:
                similarity = np.dot(background_embedding, paper_emb) / (
                    np.linalg.norm(background_embedding) * np.linalg.norm(paper_emb) + 1e-8
                )
                similarities.append(similarity)

            sorted_papers = sorted(
                zip(papers, similarities),
                key=lambda x: x[1],
                reverse=True
            )

            return [paper for paper, _ in sorted_papers]

        except Exception as e:
            print(f"⚠️  语义重排序失败: {e}，返回原始顺序")
            return papers

    def hybrid_retrieve(self, query_text: str, keywords: List[str]) -> List[Dict]:
        """
        混合检索策略 - 优先使用Semantic Scholar API，失败时自动fallback到OpenAlex
        """
        if len(keywords) == 1:
            query = keywords[0]
        else:
            query = " | ".join(f'"{item}"' for item in keywords)

        import concurrent.futures

        newest_papers = []
        highly_cited_papers = []
        relevant_papers = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_newest = executor.submit(self.get_newest_paper, query)
            future_highly_cited = executor.submit(self.get_highly_cited_paper, query)
            future_relevant = executor.submit(self.get_relevant_paper, query)

            try:
                newest_papers = future_newest.result(timeout=120)
            except Exception:
                newest_papers = []

            try:
                highly_cited_papers = future_highly_cited.result(timeout=120)
            except Exception:
                highly_cited_papers = []

            try:
                relevant_papers = future_relevant.result(timeout=120)
            except Exception:
                relevant_papers = []

        results = {
            "newest_papers": newest_papers or [],
            "highly_cited_papers": highly_cited_papers or [],
            "relevant_papers": relevant_papers or []
        }
        all_papers = self.merge_and_deduplicate(results)

        if not all_papers:
            return []

        if self.embedding_client:
            try:
                background_embedding = self.embedding_client.encode(query_text, show_progress_bar=False)
                if background_embedding is not None and len(background_embedding) > 0:
                    all_papers = self.rerank_by_similarity(all_papers, background_embedding, query_text)
            except Exception as e:
                print(f"⚠️  语义重排序失败: {e}，使用原始顺序")

        return all_papers[:self.config.MAX_TOTAL_PAPERS]

