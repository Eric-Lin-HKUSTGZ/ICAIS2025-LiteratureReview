"""
Prompt模板 - 用于文献综述系统的各个阶段
"""
import re


def detect_language(text: str) -> str:
    """检测文本语言，返回'zh'（中文）或'en'（英文）"""
    if not text:
        return 'en'
    
    # 统计中文字符数量
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # 统计总字符数量（排除空格和标点）
    total_chars = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', text))
    
    if total_chars == 0:
        return 'en'
    
    # 如果中文字符占比超过30%，认为是中文
    if chinese_chars / total_chars > 0.3:
        return 'zh'
    else:
        return 'en'


def get_keyword_extraction_prompt(query: str, language: str = 'en') -> str:
    """关键词提取Prompt"""
    if language == 'zh':
        prompt = f"""你是一位学术研究专家。请从以下用户查询中提取3-4个核心英文关键词，用于学术论文检索。

用户查询：{query}

要求：
1. 提取3-4个核心英文关键词
2. 关键词应该是名词或名词短语
3. 关键词应该能够准确反映用户感兴趣的研究领域
4. 关键词应该适合用于学术论文检索（如Semantic Scholar、OpenAlex等）

请只返回关键词，用逗号分隔，不要有其他文字。例如：transformer models, attention mechanism, deep learning"""
    else:
        prompt = f"""You are an expert in academic research. Please extract 3-4 core English keywords from the following user query for academic paper retrieval.

User Query: {query}

Requirements:
1. Extract 3-4 core English keywords
2. Keywords should be nouns or noun phrases
3. Keywords should accurately reflect the research area the user is interested in
4. Keywords should be suitable for academic paper retrieval (e.g., Semantic Scholar, OpenAlex)

Please return only the keywords, separated by commas, without any other text. Example: transformer models, attention mechanism, deep learning"""
    
    return prompt


def get_domain_analysis_prompt(query: str, keywords: list, language: str = 'en') -> str:
    """领域分析Prompt"""
    keywords_str = ", ".join(keywords)
    if language == 'zh':
        prompt = f"""你是一位学术研究专家。请分析以下用户查询，理解其研究领域和主题范围。

用户查询：{query}
提取的关键词：{keywords_str}

请提供：
1. 研究领域的描述（100-200字）
2. 主要研究主题和子领域
3. 该领域的重要性

请使用中文回答。"""
    else:
        prompt = f"""You are an expert in academic research. Please analyze the following user query to understand its research domain and topic scope.

User Query: {query}
Extracted Keywords: {keywords_str}

Please provide:
1. Description of the research domain (100-200 words)
2. Main research topics and sub-domains
3. Importance of this field

Please respond in English."""
    
    return prompt


def get_paper_classification_prompt(papers: list, query: str, language: str = 'en') -> str:
    """论文分类Prompt"""
    papers_text = ""
    # 限制论文数量，并截断摘要长度以避免prompt过长
    for i, paper in enumerate(papers[:20], 1):
        title = paper.get('title', '')
        abstract = paper.get('abstract', '') or ''
        # 限制摘要长度为200字符，避免prompt过长
        if len(abstract) > 200:
            abstract = abstract[:200] + "..."
        papers_text += f"\n论文 {i}:\n标题: {title}\n摘要: {abstract}\n"
    
    if language == 'zh':
        prompt = f"""你是一位学术研究专家。请对以下论文进行分类和筛选，找出与用户查询最相关和最重要的论文。

用户查询：{query}

论文列表：
{papers_text}

请：
1. 按主题/方法/应用领域对论文进行分类
2. 筛选出最相关和最重要的论文（最多10-15篇）
3. 为每篇论文标注分类标签

请使用中文回答，以列表形式输出分类结果。"""
    else:
        prompt = f"""You are an expert in academic research. Please classify and filter the following papers to identify the most relevant and important papers related to the user query.

User Query: {query}

Paper List:
{papers_text}

Please:
1. Classify papers by topic/method/application domain
2. Filter out the most relevant and important papers (up to 10-15 papers)
3. Label each paper with classification tags

Please respond in English, output the classification results in list format."""
    
    return prompt


def get_paper_summary_prompt(paper: dict, query: str, language: str = 'en') -> str:
    """论文总结Prompt"""
    title = paper.get('title', '')
    abstract = paper.get('abstract', '') or ''
    
    if language == 'zh':
        prompt = f"""你是一位学术研究专家。请对以下论文进行结构化总结，提取与用户查询相关的关键信息。

用户查询：{query}

论文信息：
标题：{title}
摘要：{abstract}

请提供结构化总结，包括：
1. 标题
2. 摘要
3. 主要方法
4. 核心贡献
5. 主要结论
6. 与用户查询的相关性

请使用中文回答。"""
    else:
        prompt = f"""You are an expert in academic research. Please provide a structured summary of the following paper, extracting key information relevant to the user query.

User Query: {query}

Paper Information:
Title: {title}
Abstract: {abstract}

Please provide a structured summary including:
1. Title
2. Abstract
3. Main Methods
4. Core Contributions
5. Main Conclusions
6. Relevance to User Query

Please respond in English."""
    
    return prompt


def get_topic_clustering_prompt(summaries: list, language: str = 'en') -> str:
    """主题聚类Prompt"""
    summaries_text = ""
    # 限制总结数量，并截断过长的总结
    for i, summary in enumerate(summaries[:15], 1):
        # 限制每个总结的长度为500字符，避免prompt过长
        if len(summary) > 500:
            summary = summary[:500] + "..."
        summaries_text += f"\n论文 {i} 总结:\n{summary}\n"
    
    if language == 'zh':
        prompt = f"""你是一位学术研究专家。请基于以下论文总结，识别研究主题和子领域。

论文总结：
{summaries_text}

请：
1. 识别主要研究主题（3-5个）
2. 识别子领域和细分方向
3. 分析各主题之间的关系

请使用中文回答，以结构化格式输出。"""
    else:
        prompt = f"""You are an expert in academic research. Please identify research topics and sub-domains based on the following paper summaries.

Paper Summaries:
{summaries_text}

Please:
1. Identify main research topics (3-5 topics)
2. Identify sub-domains and specific directions
3. Analyze relationships between topics

Please respond in English, output in structured format."""
    
    return prompt


def get_trend_analysis_prompt(papers: list, language: str = 'en') -> str:
    """趋势分析Prompt"""
    papers_text = ""
    for i, paper in enumerate(papers[:15], 1):
        title = paper.get('title', '')
        abstract = paper.get('abstract', '') or ''
        # 限制摘要长度为200字符，避免prompt过长
        if len(abstract) > 200:
            abstract = abstract[:200] + "..."
        papers_text += f"\n论文 {i}:\n标题: {title}\n摘要: {abstract}\n"
    
    if language == 'zh':
        prompt = f"""你是一位学术研究专家。请分析以下论文的研究趋势和热点。

论文列表：
{papers_text}

请：
1. 分析研究趋势（时间维度）
2. 识别研究热点和新兴方向
3. 预测未来可能的发展方向

请使用中文回答。"""
    else:
        prompt = f"""You are an expert in academic research. Please analyze research trends and hotspots from the following papers.

Paper List:
{papers_text}

Please:
1. Analyze research trends (temporal dimension)
2. Identify research hotspots and emerging directions
3. Predict possible future developments

Please respond in English."""
    
    return prompt


def get_review_generation_prompt(summaries: list, topics: str, trends: str, query: str, papers: list, language: str = 'en') -> str:
    """综述生成Prompt"""
    summaries_text = ""
    for i, summary in enumerate(summaries, 1):
        summaries_text += f"\n论文 {i}:\n{summary}\n"
    
    # 构建论文标题列表，用于参考文献
    papers_list_text = ""
    for i, paper in enumerate(papers, 1):
        title = paper.get('title', '') or ''
        if title:
            papers_list_text += f"\n论文 {i}: {title}\n"
    
    if language == 'zh':
        prompt = f"""你是一位学术研究专家。请基于以下信息生成一篇完整的文献综述。

用户查询：{query}

论文总结：
{summaries_text}

主题聚类结果：
{topics}

趋势分析结果：
{trends}

可用论文列表（用于参考文献）：
{papers_list_text}

CRITICAL REQUIREMENT - PAPER CITATION FORMAT:
- 在综述正文中引用论文时，使用编号引用格式（例如 [1], [2], [3]）
- 引用编号必须从[1]开始，按照论文在正文中首次出现的顺序连续编号
- 引用编号必须连续（1, 2, 3, 4, 5...），不能有间隔或跳过
- 不要在正文中使用"论文1"、"论文2"或"论文X"这样的通用引用
- 在综述末尾，包含一个"参考文献"部分，列出所有在正文中引用的论文的完整标题
- 参考文献格式为：[1] [完整论文标题], [2] [完整论文标题], [3] [完整论文标题] 等
- 参考文献编号必须连续从[1]到[N]，与正文中使用的引用编号匹配
- 只包含在正文中实际引用的论文

请生成一篇结构化的文献综述，包括：
1. 引言：介绍研究领域和背景（使用编号引用 [1], [2] 等）
2. 研究现状：综述当前研究状况（使用编号引用 [1], [2] 等）
3. 主要方法：总结主要研究方法和技术（使用编号引用 [1], [2] 等）
4. 应用领域：介绍主要应用领域（使用编号引用 [1], [2] 等）
5. 发展趋势：分析研究趋势和未来方向（使用编号引用 [1], [2] 等）
6. 总结：总结全文
7. 参考文献：列出所有引用的论文，格式为 [1] [完整论文标题], [2] [完整论文标题] 等

IMPORTANT OUTPUT FORMAT REQUIREMENTS:
- 使用Markdown格式
- 直接开始综述内容，不要包含"当然"、"根据"等介绍性短语
- 不要包含关于写作过程的元评论（如"我已经"、"我将"、"让我"等）
- 不要包含文件名、元数据或其他无关内容
- 只输出综述内容本身，从第一个章节标题开始（如"## 引言"）
- 在正文中使用编号引用 [1], [2], [3] 等引用论文，引用编号必须从[1]开始连续编号，不能有间隔
- 在末尾包含参考文献部分，列出所有引用的论文的完整标题，编号从[1]到[N]连续，与正文中的引用编号匹配
- 确保内容详实、逻辑清晰"""
    else:
        prompt = f"""You are an expert in academic research. Please generate a complete literature review based on the following information.

User Query: {query}

Paper Summaries:
{summaries_text}

Topic Clustering Results:
{topics}

Trend Analysis Results:
{trends}

Available Papers List (for references):
{papers_list_text}

CRITICAL REQUIREMENT - PAPER CITATION FORMAT:
- When referencing papers in the review body, use numbered citations in square brackets (e.g., [1], [2], [3])
- Citation numbers MUST be assigned sequentially starting from [1] based on the order papers are FIRST mentioned in the review body
- Citation numbers MUST be continuous (1, 2, 3, 4, 5...), with NO gaps or skipped numbers
- DO NOT use generic references like "Paper 1", "Paper 2", or "Paper X" in the body text
- At the end of the review, include a "References" section that lists all cited papers with their full titles
- Format references as: [1] [Full Paper Title], [2] [Full Paper Title], [3] [Full Paper Title], etc.
- References MUST be numbered sequentially from [1] to [N] with NO gaps, matching the citation numbers used in the body text
- Only include papers that are actually cited in the review body

Please generate a structured literature review including:
1. Introduction: Introduce the research field and background (use numbered citations [1], [2], etc.)
2. Current Research Status: Review the current state of research (use numbered citations [1], [2], etc.)
3. Main Methods: Summarize main research methods and techniques (use numbered citations [1], [2], etc.)
4. Application Domains: Introduce main application domains (use numbered citations [1], [2], etc.)
5. Development Trends: Analyze research trends and future directions (use numbered citations [1], [2], etc.)
6. Conclusion: Summarize the entire review
7. References: List all cited papers in the format [1] [Full Paper Title], [2] [Full Paper Title], etc.

IMPORTANT OUTPUT FORMAT REQUIREMENTS:
- Use Markdown format
- Start directly with the review content. Do NOT include any introductory phrases such as "Of course", "Certainly", "Based on", "According to", etc.
- Do NOT include any meta-commentary about the writing process (e.g., "I have", "I will", "Let me")
- Do NOT include any file names, metadata, or irrelevant content
- Output ONLY the review content itself, beginning with the first section title (e.g., "## Introduction")
- Use numbered citations [1], [2], [3], etc. in the body text when referencing papers. Citations MUST be numbered sequentially from [1] with NO gaps
- Include a References section at the end with full paper titles, numbered sequentially from [1] to [N] with NO gaps, matching the citation numbers used in the body text
- Ensure the content is detailed and logically clear"""
    
    return prompt

