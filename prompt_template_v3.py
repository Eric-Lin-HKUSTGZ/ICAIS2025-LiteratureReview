"""
Prompt模板 v3 - 加强版文献综述生成方案
继续沿用纯Prompt模式，强调章节结构与引用规范
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


def get_query_understanding_prompt(query: str, language: str = 'en') -> str:
    """阶段1：查询理解与知识规划Prompt"""
    if language == 'zh':
        prompt = f"""你是一位资深的学术研究专家，拥有深厚的学术背景和丰富的文献综述写作经验。请深度分析以下用户查询，并规划一篇高质量文献综述的知识结构。

用户查询：{query}

请完成以下任务：

1. **深度理解查询意图**：
   - 如果查询中包含缩写词（如VLA、LLM、NLP等），请明确指出该缩写词在查询上下文中的完整技术名称
   - 如果查询中没有缩写词，请提供该技术的完整名称
   - 例如：如果查询是"VLA技术最新发展"，在AI/机器学习领域，VLA通常指"Vision-Language Models"（视觉语言模型），而不是"Very Large Array"（甚大阵列）
   - 明确指出该技术所属的研究领域（如人工智能、计算机视觉、自然语言处理、机器学习等）

2. **规划综述的知识结构**：
   请规划一篇高质量文献综述应该包含的知识点和结构，包括：
   - 核心概念和技术定义
   - 历史发展脉络（重要里程碑）
   - 主要技术路线和架构演进
   - 代表性模型和系统（列出具体的模型名称，如BLIP、LLaVA、GPT-4V等）
   - 关键技术突破和创新点
   - 主要应用领域和实际案例
   - 当前面临的挑战和局限性
   - 未来发展趋势和研究方向

3. **列出关键信息点**：
   请列出至少15-20个关键信息点，这些信息点应该包括：
   - 具体模型名称和发表年份
   - 关键技术细节和创新点
   - 重要应用场景
   - 关键挑战和解决方案
   - 未来研究方向

请按照以下格式输出：
技术全称：[完整技术名称]
研究领域：[领域名称]
核心概念：[核心概念1, 核心概念2, ...]
知识结构规划：
- 引言部分应涵盖：[要点1, 要点2, ...]
- 历史发展部分应涵盖：[要点1, 要点2, ...]
- 技术架构部分应涵盖：[要点1, 要点2, ...]
- 代表性模型部分应涵盖：[模型1, 模型2, ...]
- 应用领域部分应涵盖：[领域1, 领域2, ...]
- 挑战与局限性部分应涵盖：[挑战1, 挑战2, ...]
- 未来趋势部分应涵盖：[趋势1, 趋势2, ...]
关键信息点：
1. [信息点1]
2. [信息点2]
...
"""
    else:
        prompt = f"""You are a senior academic research expert with deep academic background and rich experience in writing literature reviews. Please deeply analyze the following user query and plan the knowledge structure for a high-quality literature review.

User Query: {query}

Please complete the following tasks:

1. **Deep Understanding of Query Intent**:
   - If the query contains abbreviations (e.g., VLA, LLM, NLP), please clearly identify the full technical name of the abbreviation in the query context
   - If the query has no abbreviations, please provide the full name of the technology
   - Example: If the query is "latest developments in VLA technology", in the AI/machine learning field, VLA typically refers to "Vision-Language Models", not "Very Large Array"
   - Clearly identify the research domain this technology belongs to (e.g., artificial intelligence, computer vision, natural language processing, machine learning)

2. **Plan the Knowledge Structure of the Review**:
   Please plan the knowledge points and structure that a high-quality literature review should include:
   - Core concepts and technical definitions
   - Historical development trajectory (important milestones)
   - Main technical routes and architecture evolution
   - Representative models and systems (list specific model names, such as BLIP, LLaVA, GPT-4V, etc.)
   - Key technical breakthroughs and innovations
   - Main application domains and practical cases
   - Current challenges and limitations
   - Future development trends and research directions

3. **List Key Information Points**:
   Please list at least 15-20 key information points, which should include:
   - Specific model names and publication years
   - Key technical details and innovations
   - Important application scenarios
   - Key challenges and solutions
   - Future research directions

Please output in the following format:
Full Name: [Full technical name]
Research Domain: [Domain name]
Core Concepts: [Concept1, Concept2, ...]
Knowledge Structure Plan:
- Introduction section should cover: [Point1, Point2, ...]
- Historical development section should cover: [Point1, Point2, ...]
- Technical architecture section should cover: [Point1, Point2, ...]
- Representative models section should cover: [Model1, Model2, ...]
- Application domains section should cover: [Domain1, Domain2, ...]
- Challenges and limitations section should cover: [Challenge1, Challenge2, ...]
- Future trends section should cover: [Trend1, Trend2, ...]
Key Information Points:
1. [Information point 1]
2. [Information point 2]
...
"""
    
    return prompt


def get_literature_review_generation_prompt(query: str, knowledge_plan: str, language: str = 'en') -> str:
    """阶段2：文献综述生成Prompt - v3版本强调章节完整性与引用规范"""
    if language == 'zh':
        prompt = f"""你是一位资深的学术研究专家。请基于以下查询与知识规划，生成一篇3000-3800字的高质量文献综述，并确保具备严谨的章节结构、叙述型引用以及规范的参考文献列表。

用户查询：{query}

知识规划：
{knowledge_plan}

### 一、章节与篇幅要求（必须严格遵守）
综述须按以下顺序组织，每章必须以带数字的标题呈现（示例：“## 2 模型与架构演进”、“### 2.1 自注意力机制”），但“参考文献”章节标题禁止带数字（直接写“## 参考文献”）；各部分写作范围不可显著低于要求长度：
1. **标题**：学术化且包含技术关键词，必须使用Markdown一级标题（以“# ”开头）。
2. **摘要（约300-350字）**：三段式撰写，说明背景、核心贡献与关键结论；摘要结尾另起一行写“索引词—关键词1, 关键词2, …”列出3-5个关键词。
3. **引言（约400-500字）**：涵盖背景价值、研究动机、综述范围与章节组织。
4. **历史基础与代表性里程碑（约450-550字）**：按时间线概述关键模型/算法，突出突破点。
5. **模型与架构演进（约500-600字）**：对比不同架构范式（如基于CNN、Transformer、基础模型），至少包含一张Markdown表格对比结构、代表工作、优势与局限。
6. **训练策略与算法方法（约450-550字）**：讨论预训练、对齐、指令调优等方法论，并用另一张表格总结策略与典型模型。
7. **应用与系统落地（约450-550字）**：选择≥3个应用领域（如医疗、自动驾驶、多模态对话），说明任务场景、性能指标与实际案例。
8. **评估体系与实验观察（约350-450字）**：梳理指标、基准数据集，解释性能差异。
9. **挑战与未来展望（约350-450字）**：分条说明技术瓶颈、开放问题与趋势。
10. **总结（约200字）**：概括核心发现与研究建议。
11. **参考文献**：标题必须写作“## 参考文献”且不带编号；列出与正文引用一一对应的文献，数量不少于10条。

### 二、叙述型引用规则（CRITICAL）
- 在正文首次引用某论文/模型时，必须采用“作者姓氏 + 等/年份 + 编号”形式，例如：Parmar等人 [3] 提出了Image Transformer……或 “Parmar et al. [3] proposed the Image Transformer …”。确保句子读起来通顺，切勿仅写“[3] 提出了……”
- 引用编号从[1]开始递增，按首次出现顺序排序；后续再次引用同一文献沿用原编号。
- 在关键论述段落中优先使用“作者 + 描述 + [编号]”的叙述形式，避免堆砌式引用。

### 三、参考文献格式（严格仿照示例）
在“参考文献”章节中，按照以下模板列出正文中出现的全部文献：
[n] F. Rosenblatt, *The Perceptron, a Perceiving and Recognizing Automaton*. Cornell Aeronautical Lab., Buffalo, NY, USA, 1957.
[n+1] A. Krizhevsky, I. Sutskever, and G. E. Hinton, “ImageNet classification with deep convolutional neural networks,” *Proc. NIPS*, 2012, pp. 1097–1105.
要求：
- 作者姓名写成“首字母. 姓氏”或“姓氏, 名字首字母”形式；多名作者以逗号+and连接，超过3位可写“et al.”
- 标题加引号或斜体保持一致；列出会议/期刊/出版机构、年份、卷期号（若有）及页码。
- 仅列出正文真正引用的文献，且与编号完全对应。

### 四、内容深度与数据要求
- 报道至少12项具体模型/算法，并给出对应年份、核心贡献或数据表现。
- 在“应用与系统落地”或“评估体系与实验观察”章节中，至少给出一段量化指标（如BLEU、CIDEr、Top-1 Acc.）。
- 说明各章节逻辑衔接，如从历史铺垫到当前方法，再到挑战与展望。
- 语言需学术、客观、无第一人称与写作过程描述。

### 五、输出格式
- 使用Markdown，文章首行必须是一级标题（例如“# Vision Transformers: …”）。除“参考文献”外的后续章节标题用“##”并在标题中显式编号（如“## 3 历史基础与代表性里程碑”）；子标题使用“###/####”并继续编号（如“### 3.2 Transformer关键突破”）。参考文献标题写“## 参考文献”，不得包含编号。
- 在“摘要”章节末尾单独一行写出“索引词—关键词1, 关键词2, …”。
- 表格使用标准Markdown语法。
- 直接输出综述内容，无额外解释性文字。

请严格依照上述规格生成综述。"""
    else:
        prompt = f"""You are a senior academic researcher. Using the query and knowledge plan below, craft a 2,000-2,300 word literature review that features well-defined sections, narrative in-text citations, and formally formatted references.

User Query: {query}

Knowledge Plan:
{knowledge_plan}

### 1. Section Blueprint (follow the order exactly)
All top-level headings must be numbered (e.g., “## 2 Architectural Advances”), and sub-sections should inherit numbering such as “### 2.1 Self-Attention”. The only exception is the References section, whose heading must be `## References` without any leading number.
1. **Title** – scholarly and keyword-rich, rendered as a level-one Markdown heading (`# Title`).
2. **Abstract (200-230 words)** – three paragraphs covering background, summary of coverage/method, and key findings; after the paragraphs add a standalone line “Index Terms—Term1, Term2, …” listing 3-5 keywords.
3. **Introduction (250-300 words)** – motivate the topic, clarify scope, preview the structure.
4. **Historical Foundations & Milestones (250-300 words)** – chronological narrative of seminal work with explicit breakthroughs.
5. **Architectural Advances (300-350 words)** – contrast major paradigms (e.g., CNN, Transformer, foundation models). Include at least one Markdown table enumerating architecture family, representative papers, strengths, limitations.
6. **Training Strategies & Algorithmic Techniques (250-300 words)** – cover pre-training, alignment, instruction tuning, optimization tricks. Provide another table summarizing strategies vs. signature contributions.
7. **Application Domains & Systems (250-300 words)** – detail ≥3 application areas with scenario description, metrics, and case studies.
8. **Evaluation Protocols & Empirical Insights (200-250 words)** – describe metrics, datasets, comparative results, highlighting quantitative trends.
9. **Challenges and Future Outlook (200-250 words)** – enumerate open issues, research gaps, and near-term opportunities.
10. **Conclusion (120-150 words)** – synthesize insights and actionable recommendations.
11. **References** – heading must be written as “## References” (no numeric prefix) and list ≥10 entries aligned with in-text citations.

### 2. Narrative Citation Rules (CRITICAL)
- When citing a work, embed the author(s) plus bracketed index inside the sentence, e.g., “Parmar et al. [7] introduced the Image Transformer …” or “Dosovitskiy et al. [4] demonstrated …”.
- Citation numbers start at [1] and increase by order of first appearance; reuse the same number for later mentions.
- Do not use nameless citations like “[5] shows…”. Always mention at least one author or organization in the prose.

### 3. Reference Formatting
Use IEEE-like entries mirroring the user sample:
[1] F. Rosenblatt, *The Perceptron, a Perceiving and Recognizing Automaton*. Cornell Aeronautical Lab., Buffalo, NY, USA, 1957.
[2] A. Krizhevsky, I. Sutskever, and G. E. Hinton, “ImageNet classification with deep convolutional neural networks,” *Proc. NIPS*, 2012, pp. 1097–1105.
Guidelines:
- Author names as initials + surnames; if >3 authors, “et al.” is acceptable.
- Include year, venue/publisher, location (if applicable), and page range/volume.
- Only list works that appear in the body text; numbering must align with citations.

### 4. Content & Evidence Requirements
- Mention at least 12 concrete models/algorithms with years and distinguishing contributions.
- Provide quantitative evidence (metrics, parameter counts, benchmark scores) in the Applications or Evaluation sections.
- Maintain logical transitions from history → methods → applications → challenges → outlook.
- Academic tone only; avoid first-person or process commentary.

- Use Markdown where the very first line is a level-one title (`# …`). Subsequent numbered sections use “## N …” (except the unnumbered “## References”), and subheadings continue with “### N.M …”.
- End the Abstract section with a single line “Index Terms—Term1, Term2, …”.
- Provide at least two Markdown tables (one in Architectural Advances, one in Training Strategies or Applications).
- Output only the review (no extra explanations).

Generate the review strictly following the above blueprint."""
    
    return prompt

