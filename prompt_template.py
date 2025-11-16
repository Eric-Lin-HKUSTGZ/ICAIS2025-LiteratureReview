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


def get_query_intent_analysis_prompt(query: str, language: str = 'en') -> str:
    """查询意图分析Prompt - 深度理解查询意图，消除歧义"""
    if language == 'zh':
        prompt = f"""你是一位学术研究专家。请深度分析以下用户查询的真实意图，特别关注缩写词、技术术语的歧义问题。

用户查询：{query}

请提供以下信息：

1. 技术全称：
   - 如果查询中包含缩写词（如VLA、LLM、NLP等），请提供该缩写词在查询上下文中的完整技术名称
   - 如果查询中没有缩写词，请提供该技术的完整名称
   - 例如：如果查询是"VLA技术最新发展"，在AI/机器学习领域，VLA通常指"Vision-Language Models"（视觉语言模型），而不是"Very Large Array"（甚大阵列）

2. 研究领域：
   - 明确指出该技术所属的研究领域（如人工智能、计算机视觉、自然语言处理、机器学习等）
   - 如果可能涉及多个领域，请说明主要领域和次要领域

3. 关键概念：
   - 列出3-5个与该技术相关的核心概念和术语
   - 这些概念应该能够帮助准确理解查询意图

4. 歧义澄清：
   - 如果查询中的术语可能存在歧义（如缩写词在不同领域有不同含义），请明确指出可能的歧义
   - 说明在查询的上下文中，应该采用哪种解释
   - 例如：VLA在射电天文学中指"Very Large Array"，但在AI领域指"Vision-Language Models"

5. 推荐关键词：
   - 基于以上分析，推荐3-5个用于学术论文检索的英文关键词
   - 关键词应该使用技术全称或明确的术语，避免使用可能产生歧义的缩写词
   - 关键词应该包含领域限定词，以提高检索准确性
   - 例如：如果查询是"VLA技术最新发展"，推荐关键词应该是"vision language models"、"multimodal learning"、"visual language understanding"等，而不是"VLA"

请按照以下格式输出：
技术全称：[完整技术名称]
研究领域：[领域名称]
关键概念：[概念1, 概念2, 概念3]
歧义澄清：[澄清说明]
推荐关键词：[关键词1, 关键词2, 关键词3, 关键词4]"""
    else:
        prompt = f"""You are an expert in academic research. Please deeply analyze the true intent of the following user query, with special attention to ambiguity issues with abbreviations and technical terms.

User Query: {query}

Please provide the following information:

1. Full Name:
   - If the query contains abbreviations (e.g., VLA, LLM, NLP), please provide the full technical name of the abbreviation in the query context
   - If the query has no abbreviations, please provide the full name of the technology
   - Example: If the query is "latest developments in VLA technology", in the AI/machine learning field, VLA typically refers to "Vision-Language Models", not "Very Large Array"

2. Research Domain:
   - Clearly identify the research domain this technology belongs to (e.g., artificial intelligence, computer vision, natural language processing, machine learning)
   - If multiple domains are possible, please indicate the primary and secondary domains

3. Key Concepts:
   - List 3-5 core concepts and terms related to this technology
   - These concepts should help accurately understand the query intent

4. Disambiguation:
   - If terms in the query may have ambiguity (e.g., abbreviations with different meanings in different fields), please clearly identify possible ambiguities
   - Explain which interpretation should be adopted in the query context
   - Example: VLA refers to "Very Large Array" in radio astronomy, but "Vision-Language Models" in AI

5. Recommended Keywords:
   - Based on the above analysis, recommend 3-5 English keywords for academic paper retrieval
   - Keywords should use full technical names or clear terms, avoiding abbreviations that may cause ambiguity
   - Keywords should include domain qualifiers to improve retrieval accuracy
   - Example: If the query is "latest developments in VLA technology", recommended keywords should be "vision language models", "multimodal learning", "visual language understanding", etc., not "VLA"

Please output in the following format:
Full Name: [Full technical name]
Research Domain: [Domain name]
Key Concepts: [Concept1, Concept2, Concept3]
Disambiguation: [Clarification]
Recommended Keywords: [Keyword1, Keyword2, Keyword3, Keyword4]"""
    
    return prompt


def get_keyword_extraction_prompt(query: str, intent_result: dict = None, language: str = 'en') -> str:
    """关键词提取Prompt - 基于意图分析结果生成更准确的关键词"""
    if intent_result:
        # 如果有意图分析结果，使用推荐的关键词作为基础
        recommended_keywords = intent_result.get("recommended_keywords", [])
        full_name = intent_result.get("full_name", "")
        domain = intent_result.get("domain", "")
        disambiguation = intent_result.get("disambiguation", "")
        
        if language == 'zh':
            prompt = f"""你是一位学术研究专家。请基于以下查询意图分析结果，提取3-4个核心英文关键词用于学术论文检索。

用户查询：{query}

查询意图分析结果：
- 技术全称：{full_name}
- 研究领域：{domain}
- 歧义澄清：{disambiguation}
- 推荐关键词：{', '.join(recommended_keywords) if recommended_keywords else '无'}

要求：
1. 优先使用意图分析中推荐的关键词，但可以根据需要进行调整
2. 确保关键词使用技术全称或明确术语，避免可能产生歧义的缩写词
3. 关键词应该包含领域限定词，以提高检索准确性
4. 提取3-4个核心英文关键词，用逗号分隔

请只返回关键词，用逗号分隔，不要有其他文字。"""
        else:
            prompt = f"""You are an expert in academic research. Please extract 3-4 core English keywords for academic paper retrieval based on the following query intent analysis.

User Query: {query}

Query Intent Analysis:
- Full Name: {full_name}
- Research Domain: {domain}
- Disambiguation: {disambiguation}
- Recommended Keywords: {', '.join(recommended_keywords) if recommended_keywords else 'None'}

Requirements:
1. Prioritize the recommended keywords from the intent analysis, but adjust as needed
2. Ensure keywords use full technical names or clear terms, avoiding abbreviations that may cause ambiguity
3. Keywords should include domain qualifiers to improve retrieval accuracy
4. Extract 3-4 core English keywords, separated by commas

Please return only the keywords, separated by commas, without any other text."""
    else:
        # 如果没有意图分析结果，使用原来的prompt
        if language == 'zh':
            prompt = f"""你是一位学术研究专家。请从以下用户查询中提取3-4个核心英文关键词，用于学术论文检索。

用户查询：{query}

要求：
1. 提取3-4个核心英文关键词
2. 关键词应该是名词或名词短语
3. 关键词应该能够准确反映用户感兴趣的研究领域
4. 关键词应该适合用于学术论文检索（如Semantic Scholar、OpenAlex等）
5. 如果查询中包含缩写词，请使用技术全称而非缩写词

请只返回关键词，用逗号分隔，不要有其他文字。例如：transformer models, attention mechanism, deep learning"""
        else:
            prompt = f"""You are an expert in academic research. Please extract 3-4 core English keywords from the following user query for academic paper retrieval.

User Query: {query}

Requirements:
1. Extract 3-4 core English keywords
2. Keywords should be nouns or noun phrases
3. Keywords should accurately reflect the research area the user is interested in
4. Keywords should be suitable for academic paper retrieval (e.g., Semantic Scholar, OpenAlex)
5. If the query contains abbreviations, use full technical names instead of abbreviations

Please return only the keywords, separated by commas, without any other text. Example: transformer models, attention mechanism, deep learning"""
    
    return prompt


def get_domain_analysis_prompt(query: str, keywords: list, intent_result: dict = None, language: str = 'en') -> str:
    """领域分析Prompt - 增强版，要求输出技术全称、相关领域、关键概念、可能的歧义澄清"""
    keywords_str = ", ".join(keywords)
    
    if intent_result:
        full_name = intent_result.get("full_name", "")
        domain = intent_result.get("domain", "")
        key_concepts = intent_result.get("key_concepts", "")
        disambiguation = intent_result.get("disambiguation", "")
        
        if language == 'zh':
            prompt = f"""你是一位学术研究专家。请基于以下信息，深入分析用户查询的研究领域和主题范围。

用户查询：{query}
提取的关键词：{keywords_str}

查询意图分析结果：
- 技术全称：{full_name}
- 研究领域：{domain}
- 关键概念：{key_concepts}
- 歧义澄清：{disambiguation}

请提供以下内容：
1. 研究领域的详细描述（100-200字）
   - 包括该领域的历史发展、核心概念和意义
   - 说明该领域在学术研究和实际应用中的重要性

2. 主要研究主题和子领域
   - 列出3-5个主要研究主题
   - 说明每个主题的核心内容和研究方向

3. 技术全称和常见缩写
   - 明确说明该技术的完整名称
   - 列出常见的缩写形式（如果有）
   - 说明在不同上下文中可能存在的歧义

4. 关键概念和技术术语
   - 列出5-8个与该领域相关的核心概念和技术术语
   - 简要说明每个概念的含义和重要性

5. 可能的歧义和澄清
   - 如果该技术或术语在不同领域有不同含义，请明确指出
   - 说明在用户查询的上下文中，应该采用哪种解释

请使用中文回答，确保内容详实、准确。"""
        else:
            prompt = f"""You are an expert in academic research. Please deeply analyze the research domain and topic scope of the user query based on the following information.

User Query: {query}
Extracted Keywords: {keywords_str}

Query Intent Analysis:
- Full Name: {full_name}
- Research Domain: {domain}
- Key Concepts: {key_concepts}
- Disambiguation: {disambiguation}

Please provide the following:
1. Detailed description of the research domain (100-200 words)
   - Include historical development, core concepts, and significance of this field
   - Explain the importance of this field in academic research and practical applications

2. Main research topics and sub-domains
   - List 3-5 main research topics
   - Explain the core content and research directions of each topic

3. Full technical name and common abbreviations
   - Clearly state the full name of the technology
   - List common abbreviations (if any)
   - Explain possible ambiguities in different contexts

4. Key concepts and technical terms
   - List 5-8 core concepts and technical terms related to this field
   - Briefly explain the meaning and importance of each concept

5. Possible ambiguities and clarifications
   - If the technology or term has different meanings in different fields, please clearly identify them
   - Explain which interpretation should be adopted in the user query context

Please respond in English, ensuring the content is detailed and accurate."""
    else:
        if language == 'zh':
            prompt = f"""你是一位学术研究专家。请分析以下用户查询，理解其研究领域和主题范围。

用户查询：{query}
提取的关键词：{keywords_str}

请提供：
1. 研究领域的描述（100-200字）
2. 主要研究主题和子领域
3. 该领域的重要性
4. 技术全称和常见缩写（如果查询中包含缩写词）
5. 关键概念和技术术语
6. 可能的歧义和澄清

请使用中文回答。"""
        else:
            prompt = f"""You are an expert in academic research. Please analyze the following user query to understand its research domain and topic scope.

User Query: {query}
Extracted Keywords: {keywords_str}

Please provide:
1. Description of the research domain (100-200 words)
2. Main research topics and sub-domains
3. Importance of this field
4. Full technical name and common abbreviations (if the query contains abbreviations)
5. Key concepts and technical terms
6. Possible ambiguities and clarifications

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


def get_paper_validation_prompt(papers: list, query: str, intent_result: dict, language: str = 'en') -> str:
    """论文验证Prompt - 验证检索到的论文是否与查询意图匹配"""
    papers_text = ""
    for i, paper in enumerate(papers[:20], 1):  # 限制论文数量
        title = paper.get('title', '')
        abstract = paper.get('abstract', '') or ''
        if len(abstract) > 300:
            abstract = abstract[:300] + "..."
        papers_text += f"\n论文 {i}:\n标题: {title}\n摘要: {abstract}\n"
    
    full_name = intent_result.get("full_name", "")
    domain = intent_result.get("domain", "")
    disambiguation = intent_result.get("disambiguation", "")
    
    if language == 'zh':
        prompt = f"""你是一位学术研究专家。请验证以下检索到的论文是否与用户查询意图匹配。

用户查询：{query}

查询意图分析结果：
- 技术全称：{full_name}
- 研究领域：{domain}
- 歧义澄清：{disambiguation}

检索到的论文：
{papers_text}

请：
1. 评估每篇论文与查询意图的相关性（高/中/低）
2. 如果论文与查询意图不匹配（例如，论文讨论的是其他领域的技术），请明确指出
3. 如果大部分论文（超过50%）与查询意图不匹配，请说明原因
4. 推荐是否需要调整检索策略或关键词

请使用中文回答，格式如下：
论文1: [相关性评估] [简要说明]
论文2: [相关性评估] [简要说明]
...
总体评估: [是否需要重新检索] [原因]"""
    else:
        prompt = f"""You are an expert in academic research. Please validate whether the following retrieved papers match the user query intent.

User Query: {query}

Query Intent Analysis:
- Full Name: {full_name}
- Research Domain: {domain}
- Disambiguation: {disambiguation}

Retrieved Papers:
{papers_text}

Please:
1. Assess the relevance of each paper to the query intent (High/Medium/Low)
2. If a paper does not match the query intent (e.g., the paper discusses technology in other fields), please clearly identify it
3. If most papers (more than 50%) do not match the query intent, please explain the reason
4. Recommend whether retrieval strategy or keywords need adjustment

Please respond in English, in the following format:
Paper 1: [Relevance Assessment] [Brief Explanation]
Paper 2: [Relevance Assessment] [Brief Explanation]
...
Overall Assessment: [Whether re-retrieval is needed] [Reason]"""
    
    return prompt


def get_review_generation_prompt(summaries: list, topics: str, trends: str, query: str, papers: list, intent_result: dict = None, language: str = 'en') -> str:
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
    
    # 构建查询意图信息
    intent_info = ""
    if intent_result:
        full_name = intent_result.get("full_name", "")
        domain = intent_result.get("domain", "")
        disambiguation = intent_result.get("disambiguation", "")
        if full_name or domain or disambiguation:
            intent_info = f"""
查询意图分析结果（CRITICAL - 必须优先考虑）：
- 技术全称：{full_name}
- 研究领域：{domain}
- 歧义澄清：{disambiguation}

IMPORTANT: 你必须基于以上查询意图分析结果生成综述。如果中间步骤的结果（论文总结、主题聚类、趋势分析）与查询意图不匹配，你必须：
1. 优先基于原始查询意图和查询意图分析结果生成综述
2. 忽略或调整与查询意图不匹配的中间结果
3. 确保生成的综述准确反映用户查询的真实意图
"""
    
    if language == 'zh':
        prompt = f"""你是一位学术研究专家。请基于以下信息生成一篇完整的文献综述。

用户查询：{query}
{intent_info}
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

CRITICAL LENGTH REQUIREMENT:
- 综述总长度必须在3000-4000字符之间（包括参考文献部分）
- 每个章节都应该有充分的内容，确保综述详实、深入、全面
- 引言部分应该详细介绍研究领域的背景和重要性，包括历史发展、核心概念和意义（400-500字符）
- 研究现状部分应该全面综述当前研究状况，包括多个研究方向和重要成果，深入分析各方向的特点和贡献（700-900字符）
- 主要方法部分应该详细总结主要研究方法和技术，包括技术细节、创新点和优缺点分析（600-800字符）
- 应用领域部分应该介绍多个应用领域，每个领域都有具体说明、应用场景和实际案例（600-800字符）
- 发展趋势部分应该深入分析研究趋势和未来方向，包括多个维度的分析、挑战和机遇（400-600字符）
- 总结部分应该全面总结全文要点，包括主要发现和未来展望（150-200字符）
- 参考文献部分应该列出所有引用的论文（300-500字符，取决于引用数量）

IMPORTANT OUTPUT FORMAT REQUIREMENTS:
- 使用Markdown格式
- 直接开始综述内容，不要包含"当然"、"根据"等介绍性短语
- 不要包含关于写作过程的元评论（如"我已经"、"我将"、"让我"等）
- 不要包含文件名、元数据或其他无关内容
- 只输出综述内容本身，从第一个章节标题开始（如"## 引言"）
- 在正文中使用编号引用 [1], [2], [3] 等引用论文，引用编号必须从[1]开始连续编号，不能有间隔
- 在末尾包含参考文献部分，列出所有引用的论文的完整标题，编号从[1]到[N]连续，与正文中的引用编号匹配
- 确保内容详实、逻辑清晰、深入透彻
- CRITICAL: 确保综述内容准确反映用户查询的真实意图，特别是技术全称和研究领域。如果中间结果与查询意图不匹配，必须基于查询意图重新组织内容"""
    else:
        # Build query intent information for English
        intent_info_en = ""
        if intent_result:
            full_name = intent_result.get("full_name", "")
            domain = intent_result.get("domain", "")
            disambiguation = intent_result.get("disambiguation", "")
            if full_name or domain or disambiguation:
                intent_info_en = f"""
Query Intent Analysis Results (CRITICAL - Must prioritize):
- Full Name: {full_name}
- Research Domain: {domain}
- Disambiguation: {disambiguation}

IMPORTANT: You must generate the review based on the above query intent analysis results. If intermediate results (paper summaries, topic clustering, trend analysis) do not match the query intent, you must:
1. Prioritize generating the review based on the original query intent and query intent analysis results
2. Ignore or adjust intermediate results that do not match the query intent
3. Ensure the generated review accurately reflects the true intent of the user query
"""
        
        prompt = f"""You are an expert in academic research. Please generate a complete literature review based on the following information.

User Query: {query}
{intent_info_en}
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

CRITICAL LENGTH REQUIREMENT:
- The total length of the review MUST be between 3000-4000 characters (including the References section)
- Each section should have substantial content to ensure the review is comprehensive, in-depth, and thorough
- Introduction section should provide detailed background and importance of the research field, including historical development, core concepts, and significance (400-500 characters)
- Current Research Status section should comprehensively review the current state of research, including multiple research directions and important achievements, with in-depth analysis of characteristics and contributions of each direction (700-900 characters)
- Main Methods section should provide detailed summary of main research methods and techniques, including technical details, innovations, and analysis of advantages and disadvantages (600-800 characters)
- Application Domains section should introduce multiple application domains, with specific descriptions, application scenarios, and practical cases for each domain (600-800 characters)
- Development Trends section should provide in-depth analysis of research trends and future directions, including multi-dimensional analysis, challenges, and opportunities (400-600 characters)
- Conclusion section should comprehensively summarize the key points of the entire review, including main findings and future prospects (150-200 characters)
- References section should list all cited papers (300-500 characters, depending on the number of citations)

IMPORTANT OUTPUT FORMAT REQUIREMENTS:
- Use Markdown format
- Start directly with the review content. Do NOT include any introductory phrases such as "Of course", "Certainly", "Based on", "According to", etc.
- Do NOT include any meta-commentary about the writing process (e.g., "I have", "I will", "Let me")
- Do NOT include any file names, metadata, or irrelevant content
- Output ONLY the review content itself, beginning with the first section title (e.g., "## Introduction")
- Use numbered citations [1], [2], [3], etc. in the body text when referencing papers. Citations MUST be numbered sequentially from [1] with NO gaps
- Include a References section at the end with full paper titles, numbered sequentially from [1] to [N] with NO gaps, matching the citation numbers used in the body text
- Ensure the content is detailed, logically clear, comprehensive, and in-depth
- CRITICAL: Ensure the review content accurately reflects the true intent of the user query, especially the full technical name and research domain. If intermediate results do not match the query intent, you must reorganize the content based on the query intent"""
    
    return prompt

