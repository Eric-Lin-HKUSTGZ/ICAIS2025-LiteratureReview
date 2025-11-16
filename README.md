# ICAIS2025-LiteratureReview

文献调研API服务 - 基于直接pipeline流程的智能文献综述生成系统

## 文件结构

```
ICAIS2025-LiteratureReview/
├── api_service.py          # FastAPI主应用
├── config.py               # 配置管理
├── llm_client.py           # LLM客户端
├── embedding_client.py     # Embedding客户端
├── retriever.py            # 论文检索模块
├── literature_analyzer.py  # 文献分析模块
├── review_generator.py     # 综述生成模块
├── prompt_template.py      # Prompt模板
├── test_api.py             # API测试脚本
├── requirements.txt        # 依赖包
├── Dockerfile              # Docker配置
├── docker-compose.yml      # Docker Compose配置
├── .env.example            # 环境变量示例
└── README.md               # 项目说明
```

## 系统概述

本系统是一个创新的文献调研API服务，通过6步直接pipeline流程，结合混合检索、论文分类、内容总结、主题聚类和趋势分析，生成高质量的文献综述报告。

### 核心特点

1. **直接pipeline流程**：区别于多智能体架构，采用无状态、一次性的直接流程
2. **混合检索策略**：优先使用Semantic Scholar API，失败时自动fallback到OpenAlex API
3. **智能论文分析**：自动分类、总结、聚类和趋势分析
4. **语言自适应**：自动检测用户查询语言（中文/英文），所有输出适配用户语言
5. **心跳机制**：防止客户端请求超时，确保长时间任务正常完成

## 系统架构

```
用户查询 → 关键词提取 → 领域分析 → 混合检索 → 论文分类 → 内容总结 → 主题聚类 → 趋势分析 → 生成综述
```

## API接口

### 端点

```
POST http://<agent_service_host>:3000/literature_review
```

### 请求格式

```json
{
  "query": "What are the latest advances in transformer models?"
}
```

### 响应格式

SSE流式输出，OpenAI兼容格式：

```
data: {"object":"chat.completion.chunk","choices":[{"delta":{"content":"..."}}]}
data: {"object":"chat.completion.chunk","choices":[{"delta":{"content":"..."}}]}
...
data: [DONE]
```

### 输出结构

```markdown
## 文献综述

### 1. 引言
[研究领域和背景介绍]

### 2. 研究现状
[当前研究状况综述]

### 3. 主要方法
[主要研究方法和技术总结]

### 4. 应用领域
[主要应用领域介绍]

### 5. 发展趋势
[研究趋势和未来方向分析]

### 6. 总结
[全文总结]
```

## 环境配置

### 必需的环境变量

```bash
# LLM服务配置
SCI_MODEL_BASE_URL=https://api.example.com/v1
SCI_MODEL_API_KEY=your_api_key
SCI_LLM_MODEL=deepseek-ai/DeepSeek-V3
SCI_LLM_REASONING_MODEL=deepseek-ai/DeepSeek-Reasoner

# Embedding服务配置
SCI_EMBEDDING_BASE_URL=https://api.example.com/v1
SCI_EMBEDDING_API_KEY=your_embedding_api_key
SCI_EMBEDDING_MODEL=jinaai/jina-embeddings-v3
```

### 可选的环境变量

```bash
# 端口配置
HOST_PORT=3000

# 超时配置（秒）
LITERATURE_REVIEW_TIMEOUT=1200
KEYWORD_EXTRACTION_TIMEOUT=60
DOMAIN_ANALYSIS_TIMEOUT=60
RETRIEVAL_TIMEOUT=180
PAPER_CLASSIFICATION_TIMEOUT=120
PAPER_SUMMARY_TIMEOUT=300
TOPIC_CLUSTERING_TIMEOUT=120
TREND_ANALYSIS_TIMEOUT=120
REVIEW_GENERATION_TIMEOUT=480

# 论文检索配置
MAX_PAPERS_PER_QUERY=5
MAX_TOTAL_PAPERS=15
SEMANTIC_SCHOLAR_TIMEOUT=30
SEMANTIC_SCHOLAR_MAX_RETRIES=2
```

## 本地运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制`.env.example`为`.env`并填写配置：

```bash
cp .env.example .env
# 编辑.env文件，填入你的API密钥等信息
```

### 3. 运行服务

```bash
python api_service.py
```

服务将在 `http://localhost:3000` 启动

## 测试

项目提供了 `test_api.py` 测试脚本，用于测试文献综述API的流式响应。

### 基本用法

```bash
# 使用默认查询测试
python test_api.py

# 指定查询
python test_api.py --query "What are the latest advances in transformer models?"

# 使用中文查询
python test_api.py --query "transformer模型的最新进展是什么？"

# 指定API URL
python test_api.py --url http://localhost:3000/literature_review --query "Please provide a literature review on deep learning"

# 保存响应到文件
python test_api.py --query "What are the latest advances in transformer models?" --output review_result.txt

# 启用调试模式（显示详细的SSE数据解析信息）
python test_api.py --query "What are the latest advances in transformer models?" --debug
```

### 命令行参数

- `--url`: API端点URL（默认: `http://localhost:3000/literature_review`）
- `--query`: 查询字符串（默认: `"What are the latest advances in transformer models?"`）
- `--output`: 输出文件路径（可选，保存完整响应到文件）
- `--debug`: 启用调试模式，显示原始SSE数据和解析过程

### 功能特点

1. **流式响应处理**：正确处理SSE（Server-Sent Events）流式数据
2. **实时输出**：实时显示API返回的内容
3. **统计信息**：显示接收到的chunk数量、内容长度等统计信息
4. **错误处理**：完善的错误处理和超时机制（20分钟超时）
5. **调试支持**：支持调试模式，便于排查问题

### 测试示例

**英文查询测试**：
```bash
python test_api.py --query "What are the latest advances in transformer models?" --output review_en.txt
```

**中文查询测试**：
```bash
python test_api.py --query "transformer模型的最新进展是什么？" --output review_zh.txt
```

**调试模式测试**：
```bash
python test_api.py --query "deep learning in computer vision" --debug
```

### 注意事项

- 确保API服务已启动（`http://localhost:3000`）
- 测试脚本的超时时间设置为20分钟，适合长时间运行的文献综述生成任务
- 如果遇到连接错误，请检查API服务是否正常运行
- 使用 `--debug` 参数可以查看详细的SSE数据解析过程，有助于排查问题

### Docker运行

1. 构建镜像：

```bash
docker build -t icais2025-literaturereview:latest .
```

2. 运行容器：

```bash
docker run -p 3000:3000 --env-file .env icais2025-literaturereview:latest
```

## 容器化部署

系统支持使用 Docker 和 Docker Compose 进行容器化部署。

### 前置要求

1. **Docker 和 Docker Compose**：确保已安装并运行
   - 如果使用 colima，确保 colima 已启动：`colima start`
   - 如果使用 Docker Desktop，确保 Docker Desktop 正在运行

2. **基础镜像**：已通过 colima 拉取华为云镜像
   ```bash
   docker pull swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.12-slim-bookworm
   ```

3. **创建标签**：通过docker tag将华为云 SWR 的镜像重新打标签为 Docker Hub 官方格式
   ```bash
   docker tag swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.12-slim-bookworm python:3.12-slim-bookworm
   ```

### 部署步骤

#### 1. 配置环境变量

确保已创建 `.env` 文件并配置了必要的环境变量（参考上方"环境配置"章节）。

#### 2. 构建 Docker 镜像

```bash
docker-compose build
```

**说明**：
- Dockerfile 已配置使用华为云镜像：`python:3.12-slim-bookworm`
- 构建过程会自动安装 Python 依赖（使用清华镜像源加速）

#### 3. 启动服务

```bash
docker-compose up -d
```

**说明**：
- `-d` 参数表示后台运行
- 服务将在端口 3000 上启动（可通过 `HOST_PORT` 环境变量修改）

#### 4. 查看服务状态

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看最近 100 行日志
docker-compose logs --tail=100
```

#### 5. 验证服务

**健康检查**：
```bash
curl http://localhost:3000/health
```

预期响应：
```json
{
  "status": "ok",
  "service": "ICAIS2025-LiteratureReview API"
}
```

**查看 API 文档**：
访问：http://localhost:3000/docs

**测试 API 端点**：
```bash
curl -X POST http://localhost:3000/literature_review \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest advances in transformer models?"
  }' \
  --no-buffer
```

### 常用操作

#### 停止服务
```bash
docker-compose down
```

#### 重启服务
```bash
docker-compose restart
```

#### 重新构建并启动
```bash
docker-compose up -d --build
```

#### 查看实时日志
```bash
docker-compose logs -f app
```

#### 进入容器
```bash
docker-compose exec app /bin/bash
```

#### 清理资源
```bash
# 停止并删除容器
docker-compose down

# 停止并删除容器、网络、卷
docker-compose down -v

# 删除镜像（谨慎使用）
docker rmi icais2025-literaturereview:latest
```

### 容器配置说明

#### 端口配置

默认端口映射：`3000:3000`（主机端口:容器端口）

可通过环境变量修改：
```bash
# 在 .env 文件中设置
HOST_PORT=8080
```

或在 `docker-compose.yml` 中直接修改：
```yaml
ports:
  - "8080:3000"  # 主机端口:容器端口
```

#### 环境变量

所有配置通过 `.env` 文件管理，支持的环境变量请参考上方"环境配置"章节。

**重要环境变量**：
- `SCI_MODEL_BASE_URL`：LLM API 端点（必需）
- `SCI_MODEL_API_KEY`：LLM API 密钥（必需）
- `SCI_LLM_MODEL`：LLM 模型名称
- `SCI_LLM_REASONING_MODEL`：推理模型名称
- `SCI_EMBEDDING_BASE_URL`：Embedding API 端点
- `SCI_EMBEDDING_API_KEY`：Embedding API 密钥
- `SCI_EMBEDDING_MODEL`：Embedding 模型名称
- `HOST_PORT`：主机端口（默认：3000）

#### 资源限制

如需限制容器资源使用，可在 `docker-compose.yml` 中添加：

```yaml
services:
  app:
    # ... 其他配置
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 故障排除

#### 常见问题

1. **端口已被占用**
   - 错误：`bind: address already in use`
   - 解决：修改 `HOST_PORT` 环境变量或停止占用端口的服务

2. **容器无法启动**
   - 检查日志：`docker-compose logs app`
   - 检查环境变量配置是否正确
   - 确认 `.env` 文件存在且格式正确

3. **依赖安装失败**
   - 检查网络连接
   - 确认 Dockerfile 中的镜像源配置正确
   - 尝试手动构建：`docker build -t icais2025-literaturereview:latest .`

4. **服务响应超时**
   - 检查容器资源使用：`docker stats`
   - 增加超时配置（在 `.env` 文件中）
   - 检查 LLM 和 Embedding API 的连接状态

5. **API调用失败**
   - 检查环境变量中的API密钥是否正确
   - 检查网络连接是否正常
   - 查看容器日志：`docker-compose logs -f app`

### 更新服务

当代码更新后，需要重新构建并启动服务：

```bash
# 停止当前服务
docker-compose down

# 重新构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

或使用一条命令：
```bash
docker-compose up -d --build
```

**注意**：如果只修改了环境变量（`.env` 文件），只需重启服务即可，无需重新构建：
```bash
docker-compose restart
```

### 生产环境建议

1. **使用反向代理**：建议使用 Nginx 或 Traefik 作为反向代理
2. **配置 HTTPS**：使用 SSL/TLS 证书保护 API 端点
3. **监控和日志**：配置日志收集和监控系统
4. **资源限制**：根据实际负载设置合理的资源限制
5. **健康检查**：配置容器健康检查，自动重启异常容器
6. **备份配置**：定期备份 `.env` 配置文件

## 系统流程

### 步骤1: 关键词提取与领域分析

- 从用户query中提取3-4个核心英文关键词
- 分析研究领域和主题范围
- 输出：关键词列表、领域描述

### 步骤2: 混合检索论文

- 使用Semantic Scholar API检索（最新、高引用、相关论文）
- Fallback到OpenAlex API（当Semantic Scholar失败时）
- 语义重排序（基于embedding相似度）
- 输出：10-15篇相关论文

### 步骤3: 论文分类与筛选

- 按主题/方法/应用领域对论文进行分类
- 筛选最相关和最重要的论文
- 输出：分类后的论文列表

### 步骤4: 论文内容总结

- 对每篇论文进行结构化总结（标题、摘要、方法、贡献、结论）
- 提取与用户query相关的关键信息
- 输出：论文总结列表

### 步骤5: 主题聚类与趋势分析

- 识别研究主题和子领域
- 分析研究趋势和热点
- 输出：主题聚类结果、趋势分析

### 步骤6: 生成文献综述

- 基于论文总结和主题聚类生成结构化综述
- 包含：引言、研究现状、主要方法、应用领域、发展趋势、总结
- 输出：完整的文献综述报告

## 关键设计

### 1. 混合检索策略

#### 主要检索源：Semantic Scholar API
- **最新论文**：按发表时间排序
- **高引用论文**：按引用数排序
- **相关论文**：按相关性排序

#### Fallback检索源：OpenAlex API
当Semantic Scholar API失败时（特别是429错误），系统会自动切换到OpenAlex：
- **快速切换**：检测到429错误时立即切换，不进行重试
- **减少重试**：将Semantic Scholar的重试次数减少到2次，快速fallback
- **格式统一**：OpenAlex的结果自动转换为与Semantic Scholar兼容的格式
- **无缝切换**：对上层代码透明，无需修改其他逻辑

#### 语义重排序
- 基于embedding相似度重新排序所有检索到的论文
- 确保最相关的论文排在前面
- **注意**：如果未配置Embedding API（SCI_EMBEDDING_BASE_URL和SCI_EMBEDDING_API_KEY），系统将跳过语义重排序，论文将按原始检索顺序返回

### 2. 语言自动识别

- 基于中文字符占比自动检测语言
- 所有LLM调用自动使用相应语言
- 确保输入输出语言一致

### 3. 心跳机制

- 在步骤4、5、6（耗时较长的步骤）使用心跳机制
- 每25秒发送空数据chunk（`" "`）防止客户端超时
- 确保长时间任务能够正常完成

## 与deepresearch的区别

1. **架构差异**：直接pipeline vs 多智能体架构
2. **状态管理**：无状态API vs 会话管理
3. **执行方式**：一次性完成 vs 分阶段交互
4. **数据结构**：直接生成综述 vs SketchBoard概念
5. **用户交互**：无需确认 vs 需要确认大纲

## 技术栈

- **Web框架**：FastAPI
- **流式响应**：SSE (Server-Sent Events)
- **异步处理**：asyncio
- **LLM集成**：自定义API端点
- **Embedding**：OpenAI兼容API
- **论文检索**：Semantic Scholar API + OpenAlex API
- **容器化**：Docker + Docker Compose

## 许可证

本项目仅供学习和研究使用。
