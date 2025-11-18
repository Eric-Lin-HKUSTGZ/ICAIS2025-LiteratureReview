"""
Prompt模板 v2 - 纯Prompt文献综述生成方案
不使用检索API，完全依赖大模型的知识库
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
    """阶段2：文献综述生成Prompt - 优化版，继承Modex和test1110的优点"""
    if language == 'zh':
        prompt = f"""你是一位资深的学术研究专家，拥有深厚的学术背景和丰富的文献综述写作经验。请基于以下查询和知识规划，生成一篇高质量的文献综述。

用户查询：{query}

知识规划：
{knowledge_plan}

请生成一篇完整的文献综述，要求如下：

## 结构要求（必须严格遵守）

综述必须包含以下章节（按顺序），每个章节都要有充分的子章节和详细内容：

1. **标题**
   - 使用清晰、专业的学术标题
   - 格式：技术名称 + "技术最新发展综述" 或类似表述

2. **摘要**（300-400字）
   - 第一段：简要介绍研究领域的背景和重要性
   - 第二段：概述综述的主要内容和方法
   - 第三段：总结主要发现和未来展望
   - 摘要末尾需另起一行写“关键词—关键词1, 关键词2, …”，限定为3-5个技术术语（如Transformer, classification, computer vision），关键词之间用英文逗号分隔；若综述为英文，首个关键词首字母必须大写

3. **引言**（600-800字，必须包含以下子章节）
   - **研究背景与意义**：详细介绍研究领域的背景、重要性和应用价值
   - **技术发展现状概述**：概述当前技术发展的主要特征和趋势
   - **综述范围与组织结构**：说明本综述的范围、组织结构和各章节内容

4. **核心架构/技术演进**（1200-1500字，必须包含以下子章节）
   - **早期方法回顾**：详细介绍早期技术方法（如2015-2019年的代表性工作）
   - **关键技术突破历程**：按时间顺序梳理关键突破节点（2017年Transformer、2020年CLIP、2021-2023年各重要模型）
   - **最新架构设计**：详细分析当前主流架构类型（融合编码器、LLM扩展、统一架构等）
   - **技术演进脉络分析**：从技术路线、模型规模、应用场景等维度分析演进规律
   - **必须包含对比表格**：至少一个表格对比不同架构类型的特点（架构类型、代表模型、核心特点、优势、局限性）

5. **核心技术方法论**（1000-1200字，必须包含以下子章节）
   - **预训练策略与方法**：详细介绍对比学习、掩码建模、生成式预训练等方法
   - **多模态融合机制**：分析早期融合、中期融合、晚期融合以及交叉注意力机制
   - **跨模态对齐技术**：介绍全局对齐、细粒度对齐等方法
   - **指令跟随与推理能力**：分析指令调优、思维链、多步推理等技术
   - **模型扩展与优化技术**：介绍模型压缩、推理加速、训练优化等方法
   - **必须包含对比表格**：至少一个表格对比不同方法的特点

6. **特定场景与应用**（800-1000字，必须包含以下子章节）
   - **图像描述与生成场景**：详细介绍该场景的技术实现、性能表现和应用案例
   - **视觉问答与推理场景**：分析VQA任务的技术挑战和解决方案
   - **多模态对话系统**：介绍对话系统的架构和评估方法
   - **文档理解与处理**：分析文档理解的技术特点和应用
   - **必须包含性能对比表格**：至少一个表格展示不同模型在基准测试上的性能数据

7. **评估与对比分析**（600-800字，必须包含以下子章节）
   - **评估指标体系**：介绍任务导向型、能力导向型、鲁棒性评估等
   - **主流方法性能对比**：对比主要模型在关键基准测试上的表现
   - **基准测试结果分析**：深入分析不同模型在不同任务上的表现差异
   - **消融实验综述**：总结关键组件的贡献度分析
   - **必须包含性能对比表格**：至少一个表格展示模型性能对比数据

8. **挑战与未来方向**（600-800字，必须包含以下子章节）
   - **当前技术局限性**：深入分析计算效率、对齐精度、数据质量、可解释性等问题
   - **未解决的关键问题**：讨论跨模态语义鸿沟、知识推理、幻觉、安全性等问题
   - **未来研究方向展望**：从架构创新、理解深度、安全可信、持续学习等维度展望
   - **创新机遇与应用前景**：分析各应用领域的发展潜力和挑战
   - **必须包含应用领域对比表格**：至少一个表格对比不同应用领域的特点

9. **总结**（300-400字）
   - **主要发现总结**：系统总结技术发展的关键发现
   - **技术发展趋势**：概括技术演进的主要趋势
   - **研究建议与展望**：提出未来研究建议和展望

10. **参考文献**
    - 列出至少15-20篇代表性论文
    - “参考文献”章节标题必须写作“## 参考文献”，不得带编号
    - 参考条目采用IEEE风格：[n] F. Rosenblatt, *The Perceptron, a Perceiving and Recognizing Automaton*. Cornell Aeronautical Lab., Buffalo, NY, USA, 1957.
    - 仅列出正文中实际引用的文献，并按照首次出现顺序编号，编号需与正文引用一致

## 内容要求（关键质量指标）

1. **准确性和深度**：
   - 所有技术信息必须准确，模型名称、年份、技术细节必须正确
   - 内容要有深度，不能只是表面介绍
   - 技术细节要具体，包括架构设计、训练策略、创新点等

2. **具体性和详实性**（继承Modex的优点）：
   - 必须包含大量具体的模型名称（如BLIP、BLIP-2、LLaVA、LLaVA-1.5、GPT-4V、Flamingo、Qwen-VL、Shikra、CLIP、DALL-E、OFA、ViLT、ALBEF等）
   - 每个模型都要说明：发表年份、核心创新点、技术特点、主要贡献
   - 必须包含具体的技术细节：预训练策略、融合机制、对齐方法等
   - 必须包含具体的性能数据：在基准测试上的准确率、BLEU分数、CIDEr分数等
   - 必须包含具体的应用场景和案例：医疗诊断、自动驾驶、教育辅助等
   - 避免泛泛而谈，每个观点都要有具体支撑

3. **表格和对比**（继承Modex的优点）：
   - 必须包含至少4-5个对比表格：
     * 架构类型对比表（架构类型、代表模型、核心特点、优势、局限性）
     * 方法对比表（方法类型、代表模型、对齐粒度、主要技术、优势）
     * 性能对比表（模型名称、参数量、各基准测试性能）
     * 应用领域对比表（应用领域、技术需求、当前成熟度、发展潜力、主要挑战）
   - 表格要清晰、专业，包含关键对比维度
   - 表格数据要准确，与正文描述一致

4. **章节组织**（继承Modex的优点）：
   - 每个主要章节都要有清晰的子章节
   - 子章节要有明确的标题和层次结构
   - 内容要有逻辑递进关系
   - 使用Markdown格式的二级标题（##）和三级标题（###）

5. **逻辑性和连贯性**：
   - 从历史演进到当前状态再到未来趋势，逻辑清晰
   - 各章节之间要有连贯性，使用过渡句连接
   - 内容要有层次感，从宏观到微观，从理论到实践

6. **前沿性和全面性**：
   - 必须涵盖最新的研究成果（2023-2024年）
   - 必须涵盖该领域的主要研究方向
   - 不能遗漏重要的代表性工作
   - 要体现技术发展的最新趋势

7. **引用与参考文献规范**：
   - 正文引用必须采用叙述型写法（如“Radford等人 [3] 提出了CLIP模型……”），禁止仅写“[3]”
   - 引用编号自[1]起按首次出现顺序递增，后续引用沿用原编号
   - 参考文献采用IEEE格式：[n] A. Author, B. Author, “Title,” *Venue*, Year, 卷期/页码（若有）
   - “参考文献”章节标题写作“## 参考文献”，且仅包含正文实际引用的条目

## 格式要求

1. **Markdown格式**：
   - 使用标准Markdown格式
   - 顶级章节标题需采用“## N 标题”形式编号（例如“## 2 技术背景”），子章节继续编号（如“### 2.1 研究背景”）
   - “参考文献”章节标题必须写作“## 参考文献”，不得携带编号
   - 表格使用Markdown表格格式（| 列1 | 列2 |）

2. **写作风格**：
   - 直接开始内容，不要包含"当然"、"根据"、"希望这份总结对您有帮助"等介绍性或结束性短语
   - 不要包含关于写作过程的元评论（如"我已经"、"我将"、"让我"等）
   - 使用学术写作风格，客观、准确、专业
   - 语言要流畅，避免重复和冗余

3. **输出格式**：
   - 只输出综述内容本身，从标题开始
   - 不要包含任何元数据或说明文字
   - 每个章节之间用空行分隔

## 长度要求

- **总长度：6000-8000字**（包括参考文献，不包括表格）
- 每个章节都要有充分的内容，确保综述详实、深入、全面：
  - 摘要：300-400字
  - 引言：600-800字
  - 核心架构/技术演进：1200-1500字
  - 核心技术方法论：1000-1200字
  - 特定场景与应用：800-1000字
  - 评估与对比分析：600-800字
  - 挑战与未来方向：600-800字
  - 总结：300-400字
  - 参考文献：15-20条

## 质量检查清单

在生成综述前，请确保：
- [ ] 包含至少4-5个对比表格
- [ ] 每个主要章节都有清晰的子章节
- [ ] 包含至少15-20个具体模型名称
- [ ] 包含具体的性能数据和基准测试结果
- [ ] 参考文献格式规范完整
- [ ] 逻辑清晰，从历史到现状到未来
- [ ] 内容详实，避免泛泛而谈
- [ ] 技术细节准确，模型名称和年份正确

请现在开始生成文献综述，确保继承Modex.txt的详实性和表格对比优势，以及test1110.txt的简洁性和参考文献规范性："""
    else:
        prompt = f"""You are a senior academic research expert with deep academic background and rich experience in writing literature reviews. Please generate a high-quality literature review based on the following query and knowledge plan.

User Query: {query}

Knowledge Plan:
{knowledge_plan}

Please generate a complete literature review with the following requirements:

## Structure Requirements (Must Strictly Follow)

The review must include the following sections (in order), each section must have sufficient subsections and detailed content:

1. **Title**
   - Use clear, professional academic title
   - Format: Technology Name + "Latest Development Review" or similar

2. **Abstract** (300-400 words)
   - First paragraph: Briefly introduce the research field background and importance
   - Second paragraph: Overview the main content and methods of the review
   - Third paragraph: Summarize main findings and future prospects
   - After the abstract, add a standalone line “Index Terms—Term1, Term2, …” listing 3-5 technical terms (e.g., Transformer, classification, computer vision) separated by commas, ensuring the first term is capitalized

3. **Introduction** (600-800 words, must include the following subsections)
   - **Research Background and Significance**: Detailed introduction to the research field background, importance, and application value
   - **Current State of Technology Development**: Overview of main characteristics and trends in current technology development
   - **Review Scope and Organization**: Explain the scope, organization, and content of each section

4. **Core Architecture/Technical Evolution** (1200-1500 words, must include the following subsections)
   - **Early Methods Review**: Detailed introduction to early technical methods (e.g., representative works from 2015-2019)
   - **Key Technical Breakthrough Timeline**: Chronologically organize key breakthrough points (Transformer 2017, CLIP 2020, important models 2021-2023)
   - **Latest Architecture Design**: Detailed analysis of current mainstream architecture types (fusion encoders, LLM extensions, unified architectures, etc.)
   - **Technical Evolution Analysis**: Analyze evolution patterns from technical routes, model scale, application scenarios, etc.
   - **Must include comparison table**: At least one table comparing characteristics of different architecture types (architecture type, representative models, core features, advantages, limitations)

5. **Core Technical Methodologies** (1000-1200 words, must include the following subsections)
   - **Pre-training Strategies and Methods**: Detailed introduction to contrastive learning, masked modeling, generative pre-training, etc.
   - **Multimodal Fusion Mechanisms**: Analyze early fusion, mid-level fusion, late fusion, and cross-attention mechanisms
   - **Cross-modal Alignment Techniques**: Introduce global alignment, fine-grained alignment, etc.
   - **Instruction Following and Reasoning Capabilities**: Analyze instruction tuning, chain-of-thought, multi-step reasoning, etc.
   - **Model Scaling and Optimization Techniques**: Introduce model compression, inference acceleration, training optimization, etc.
   - **Must include comparison table**: At least one table comparing characteristics of different methods

6. **Specific Scenarios and Applications** (800-1000 words, must include the following subsections)
   - **Image Captioning and Generation Scenarios**: Detailed introduction to technical implementation, performance, and application cases
   - **Visual Question Answering and Reasoning Scenarios**: Analyze technical challenges and solutions for VQA tasks
   - **Multimodal Dialogue Systems**: Introduce dialogue system architectures and evaluation methods
   - **Document Understanding and Processing**: Analyze technical characteristics and applications of document understanding
   - **Must include performance comparison table**: At least one table showing performance data of different models on benchmark tests

7. **Evaluation and Comparative Analysis** (600-800 words, must include the following subsections)
   - **Evaluation Index System**: Introduce task-oriented, capability-oriented, robustness evaluation, etc.
   - **Mainstream Methods Performance Comparison**: Compare performance of main models on key benchmark tests
   - **Benchmark Test Results Analysis**: In-depth analysis of performance differences of different models on different tasks
   - **Ablation Study Summary**: Summarize contribution analysis of key components
   - **Must include performance comparison table**: At least one table showing model performance comparison data

8. **Challenges and Future Directions** (600-800 words, must include the following subsections)
   - **Current Technical Limitations**: In-depth analysis of computational efficiency, alignment accuracy, data quality, interpretability, etc.
   - **Unresolved Key Issues**: Discuss cross-modal semantic gaps, knowledge reasoning, hallucinations, safety, etc.
   - **Future Research Directions**: Look forward from architecture innovation, understanding depth, safety and trustworthiness, continuous learning, etc.
   - **Innovation Opportunities and Application Prospects**: Analyze development potential and challenges in various application fields
   - **Must include application domain comparison table**: At least one table comparing characteristics of different application domains

9. **Conclusion** (300-400 words)
   - **Main Findings Summary**: Systematically summarize key findings in technology development
   - **Technical Development Trends**: Summarize main trends in technical evolution
   - **Research Recommendations and Prospects**: Propose future research recommendations and prospects

10. **References**
    - List at least 15-20 representative papers
    - The heading must be written exactly as “## References” with no number prefix
    - Entries must follow IEEE style, e.g., “[1] F. Rosenblatt, *The Perceptron, a Perceiving and Recognizing Automaton*. Cornell Aeronautical Lab., Buffalo, NY, USA, 1957.”
    - Only include works that appear in the body text and ensure numbering matches order of first mention

## Content Requirements (Key Quality Indicators)

1. **Accuracy and Depth**:
   - All technical information must be accurate, model names, years, and technical details must be correct
   - Content must be in-depth, not just superficial introduction
   - Technical details must be specific, including architecture design, training strategies, innovations, etc.

2. **Specificity and Detail** (Inheriting Modex's advantages):
   - Must include a large number of specific model names (e.g., BLIP, BLIP-2, LLaVA, LLaVA-1.5, GPT-4V, Flamingo, Qwen-VL, Shikra, CLIP, DALL-E, OFA, ViLT, ALBEF, etc.)
   - Each model must include: publication year, core innovations, technical features, main contributions
   - Must include specific technical details: pre-training strategies, fusion mechanisms, alignment methods, etc.
   - Must include specific performance data: accuracy on benchmark tests, BLEU scores, CIDEr scores, etc.
   - Must include specific application scenarios and cases: medical diagnosis, autonomous driving, educational assistance, etc.
   - Avoid generalities, each point must have specific support

3. **Tables and Comparisons** (Inheriting Modex's advantages):
   - Must include at least 4-5 comparison tables:
     * Architecture type comparison table (architecture type, representative models, core features, advantages, limitations)
     * Method comparison table (method type, representative models, alignment granularity, main techniques, advantages)
     * Performance comparison table (model name, parameter count, performance on various benchmark tests)
     * Application domain comparison table (application domain, technical requirements, current maturity, development potential, main challenges)
   - Tables must be clear, professional, and include key comparison dimensions
   - Table data must be accurate and consistent with text descriptions

4. **Section Organization** (Inheriting Modex's advantages):
   - Each main section must have clear subsections
   - Subsections must have clear titles and hierarchical structure
   - Content must have logical progression
   - Use Markdown level 2 headings (##) and level 3 headings (###)

5. **Logic and Coherence**:
   - Clear logic from historical evolution to current state to future trends
   - Coherence between sections, use transition sentences
   - Content must have a sense of hierarchy, from macro to micro, from theory to practice

6. **Cutting-edge and Comprehensiveness**:
   - Must cover the latest research results (2023-2024)
   - Must cover the main research directions in this field
   - Must not miss important representative work
   - Must reflect the latest trends in technology development

7. **Citation and Reference Norms**:
   - Use narrative in-text citations such as “Radford et al. [3] introduced CLIP …”; do not write standalone “[3]”
   - Citation numbers start at [1], increase by first appearance, and remain consistent thereafter
   - References must follow IEEE style: “[n] A. Author, B. Author, “Title,” *Venue*, Year, vol./no./pp. (if available)”
   - The references section heading must be “## References” without numbering and include only works cited in the text

## Format Requirements

1. **Markdown Format**:
   - Use standard Markdown format
   - Number top-level sections as “## N Title” (e.g., “## 2 Technical Background”) and number subsections accordingly (e.g., “### 2.1 Early Methods”)
   - The references section heading must be “## References” without a numeric prefix
   - Tables use Markdown table format (| Column1 | Column2 |)

2. **Writing Style**:
   - Start directly with content, do not include introductory phrases such as "Of course", "Based on", "Hope this summary helps you", etc.
   - Do not include meta-commentary about the writing process (e.g., "I have", "I will", "Let me")
   - Use academic writing style, objective, accurate, and professional
   - Language must be fluent, avoid repetition and redundancy

3. **Output Format**:
   - Output only the review content itself, starting from the title
   - Do not include any metadata or explanatory text
   - Separate each section with blank lines

## Length Requirements

- **Total length: 6000-8000 words** (including references, excluding tables)
- Each section must have sufficient content to ensure the review is detailed, in-depth, and comprehensive:
  - Abstract: 300-400 words
  - Introduction: 600-800 words
  - Core Architecture/Technical Evolution: 1200-1500 words
  - Core Technical Methodologies: 1000-1200 words
  - Specific Scenarios and Applications: 800-1000 words
  - Evaluation and Comparative Analysis: 600-800 words
  - Challenges and Future Directions: 600-800 words
  - Conclusion: 300-400 words
  - References: 15-20 entries

## Quality Checklist

Before generating the review, please ensure:
- [ ] Includes at least 4-5 comparison tables
- [ ] Each main section has clear subsections
- [ ] Includes at least 15-20 specific model names
- [ ] Includes specific performance data and benchmark test results
- [ ] Reference format is standardized and complete
- [ ] Logic is clear, from history to current state to future
- [ ] Content is detailed, avoid generalities
- [ ] Technical details are accurate, model names and years are correct

Please now generate the literature review, ensuring to inherit Modex.txt's detail and table comparison advantages, as well as test1110.txt's conciseness and reference standardization:"""
    
    return prompt

