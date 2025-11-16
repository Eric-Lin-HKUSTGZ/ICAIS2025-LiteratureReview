import os
import json
import time
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import signal
import sys

from config import Config
from llm_client import LLMClient
from embedding_client import EmbeddingClient
from retriever import PaperRetriever
from literature_analyzer import LiteratureAnalyzer
from review_generator import ReviewGenerator
from prompt_template import detect_language


def load_env_file(env_file: str):
    """加载环境变量文件"""
    if not os.path.isabs(env_file):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        env_file = os.path.join(current_dir, env_file)
    
    if os.path.exists(env_file):
        print(f"✓ 找到 .env 文件: {env_file}")
        loaded_count = 0
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip('"\'')
                    loaded_count += 1
        print(f"✓ 成功加载 {loaded_count} 个环境变量")
        return True
    else:
        print(f"⚠️ 警告: 未找到 .env 文件: {env_file}")
        return False


# 加载环境变量
load_env_file(".env")

# 创建FastAPI应用
app = FastAPI(
    title="ICAIS2025-LiteratureReview API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.middleware("http")
async def simple_log_middleware(request, call_next):
    """简化的日志中间件"""
    start_time = time.time()
    path = request.url.path
    
    if not path.startswith("/health"):
        print(f"📥 [{time.strftime('%H:%M:%S')}] {request.method} {path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        if not path.startswith("/health"):
            print(f"📤 [{time.strftime('%H:%M:%S')}] {request.method} {path} - {response.status_code} ({process_time:.3f}s)")
        return response
    except Exception as e:
        print(f"❌ [{time.strftime('%H:%M:%S')}] 错误: {request.method} {path} - {e}")
        raise

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# 设置全局超时
REQUEST_TIMEOUT = Config.LITERATURE_REVIEW_TIMEOUT


class LiteratureReviewRequest(BaseModel):
    query: str


def format_sse_data(content: str) -> str:
    """生成OpenAI格式的SSE数据"""
    data = {
        "object": "chat.completion.chunk",
        "choices": [{
            "delta": {
                "content": content
            }
        }]
    }
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def format_sse_done() -> str:
    """生成SSE结束标记"""
    return "data: [DONE]\n\n"


def stream_message(message: str, chunk_size: int = 1):
    """将消息按字符流式输出（同步生成器）"""
    for i in range(0, len(message), chunk_size):
        chunk = message[i:i + chunk_size]
        yield format_sse_data(chunk)


async def run_with_heartbeat(task_func, *args, heartbeat_interval=25, **kwargs):
    """
    执行长时间任务，期间定期发送心跳数据
    
    Args:
        task_func: 要执行的同步函数
        *args, **kwargs: 传递给函数的参数
        heartbeat_interval: 心跳间隔（秒），默认25秒
    
    Yields:
        心跳数据（空格字符）或任务结果
    """
    start_time = time.time()
    last_heartbeat = start_time
    
    # 创建任务（使用asyncio.to_thread将同步函数转换为协程）
    task = asyncio.create_task(asyncio.to_thread(task_func, *args, **kwargs))
    
    # 在任务执行期间定期发送心跳
    while not task.done():
        await asyncio.sleep(1)  # 每秒检查一次
        elapsed = time.time() - last_heartbeat
        
        # 如果超过心跳间隔，发送心跳数据
        if elapsed >= heartbeat_interval:
            yield format_sse_data(" ")  # 发送一个空格作为心跳
            last_heartbeat = time.time()
        
        # 检查任务是否完成
        if task.done():
            break
    
    # 等待任务完成并返回结果
    try:
        result = await task
        # 使用特殊标记来区分结果和心跳数据
        yield ("RESULT", result)
    except Exception as e:
        print(f"⚠️  任务执行失败: {e}")
        import traceback
        print(traceback.format_exc())
        raise e


async def _generate_review_internal(query: str) -> AsyncGenerator[str, None]:
    """内部生成器函数，执行实际的文献综述生成逻辑"""
    start_time = time.time()
    
    try:
        # 先检测语言，用于后续消息模板
        language = await asyncio.to_thread(detect_language, query)
        
        # 根据语言设置消息模板
        if language == 'zh':
            msg_templates = {
                'step1': "### 📝 步骤 1/6: 关键词提取与领域分析\n\n✅ 已完成\n\n",
                'step2': lambda n: f"### 📚 步骤 2/6: 混合检索论文\n\n✅ 已检索到 {n} 篇相关论文\n\n",
                'step3': "### 🗂️ 步骤 3/6: 论文分类与筛选\n\n✅ 已完成\n\n",
                'step4': "### 📄 步骤 4/6: 论文内容总结\n\n",
                'step5': "### 🔍 步骤 5/6: 主题聚类与趋势分析\n\n",
                'step6': "### 📋 步骤 6/6: 生成文献综述\n\n",
                'final_title': "## 📄 文献综述\n\n",
                'error_no_papers': "## ❌ 错误\n\n未检索到相关论文，程序终止\n\n",
                'error_config': "## ❌ 错误\n\n配置验证失败，请检查环境变量设置\n\n",
                'error_config_exception': lambda e: f"## ❌ 错误\n\n配置验证异常: {e}\n\n",
                'error_llm_init': lambda e: f"## ❌ 错误\n\nLLM客户端初始化失败: {e}\n\n",
                'error_embedding_init': lambda e: f"## ❌ 错误\n\nEmbedding客户端初始化失败: {e}\n\n",
                'error_retriever_init': lambda e: f"## ❌ 错误\n\n论文检索器初始化失败: {e}\n\n",
                'error_timeout': lambda t: f"## ❌ 超时错误\n\n请求处理超过 {t} 秒，已自动终止\n\n",
                'error_general': lambda e: f"## ❌ 错误\n\n程序执行失败: {e}\n\n"
            }
        else:
            msg_templates = {
                'step1': "### 📝 Step 1/6: Keyword Extraction and Domain Analysis\n\n✅ Completed\n\n",
                'step2': lambda n: f"### 📚 Step 2/6: Hybrid Paper Retrieval\n\n✅ Retrieved {n} related papers\n\n",
                'step3': "### 🗂️ Step 3/6: Paper Classification and Filtering\n\n✅ Completed\n\n",
                'step4': "### 📄 Step 4/6: Paper Content Summarization\n\n",
                'step5': "### 🔍 Step 5/6: Topic Clustering and Trend Analysis\n\n",
                'step6': "### 📋 Step 6/6: Literature Review Generation\n\n",
                'final_title': "## 📄 Literature Review\n\n",
                'error_no_papers': "## ❌ Error\n\nNo related papers found. Process terminated.\n\n",
                'error_config': "## ❌ Error\n\nConfiguration validation failed. Please check environment variables.\n\n",
                'error_config_exception': lambda e: f"## ❌ Error\n\nConfiguration validation exception: {e}\n\n",
                'error_llm_init': lambda e: f"## ❌ Error\n\nLLM client initialization failed: {e}\n\n",
                'error_embedding_init': lambda e: f"## ❌ Error\n\nEmbedding client initialization failed: {e}\n\n",
                'error_retriever_init': lambda e: f"## ❌ Error\n\nPaper retriever initialization failed: {e}\n\n",
                'error_timeout': lambda t: f"## ❌ Timeout Error\n\nRequest processing exceeded {t} seconds. Automatically terminated.\n\n",
                'error_general': lambda e: f"## ❌ Error\n\nProcess execution failed: {e}\n\n"
            }
        
        # 验证配置（不输出）
        try:
            config_valid = await asyncio.to_thread(Config.validate_config)
            if not config_valid:
                for chunk in stream_message(msg_templates['error_config']):
                    yield chunk
                return
        except Exception as e:
            for chunk in stream_message(msg_templates['error_config_exception'](e)):
                yield chunk
            return
        
        # 创建组件（不输出初始化信息）
        try:
            llm_client = LLMClient()
        except Exception as e:
            for chunk in stream_message(msg_templates['error_llm_init'](e)):
                yield chunk
            return
        
        try:
            embedding_client = EmbeddingClient()
        except Exception as e:
            # Embedding客户端失败不影响主要流程，只记录警告
            print(f"⚠️  Embedding客户端初始化失败: {e}，将跳过语义重排序")
            embedding_client = None
        
        try:
            retriever = PaperRetriever()
        except Exception as e:
            for chunk in stream_message(msg_templates['error_retriever_init'](e)):
                yield chunk
            return
        
        analyzer = LiteratureAnalyzer(llm_client, language=language)
        generator = ReviewGenerator(llm_client, language=language)
        
        # 步骤1: 关键词提取与领域分析
        keywords = await asyncio.to_thread(analyzer.extract_keywords, query)
        domain_analysis = await asyncio.to_thread(analyzer.analyze_domain, query, keywords)
        for chunk in stream_message(msg_templates['step1']):
            yield chunk
        
        # 步骤2: 混合检索论文
        papers = await asyncio.to_thread(retriever.hybrid_retrieve, query, keywords)
        for chunk in stream_message(msg_templates['step2'](len(papers))):
            yield chunk
        
        if not papers:
            for chunk in stream_message(msg_templates['error_no_papers']):
                yield chunk
            return
        
        # 步骤3: 论文分类与筛选
        classified_papers = await asyncio.to_thread(analyzer.classify_papers, papers, query)
        for chunk in stream_message(msg_templates['step3']):
            yield chunk
        
        # 步骤4: 论文内容总结（使用心跳机制）
        for chunk in stream_message(msg_templates['step4']):
            yield chunk
        
        if language == 'zh':
            step4_progress = "🔄 正在总结论文内容，请稍候...\n\n"
        else:
            step4_progress = "🔄 Summarizing paper content, please wait...\n\n"
        
        for chunk in stream_message(step4_progress):
            yield chunk
        
        summaries = None
        async for item in run_with_heartbeat(
            analyzer.summarize_papers,
            classified_papers, query,
            heartbeat_interval=25
        ):
            if isinstance(item, tuple) and len(item) == 2 and item[0] == "RESULT":
                summaries = item[1]
                break
            else:
                yield item
        
        if not summaries:
            summaries = []
        
        # 步骤5: 主题聚类与趋势分析（使用心跳机制）
        for chunk in stream_message(msg_templates['step5']):
            yield chunk
        
        if language == 'zh':
            step5_progress = "🔄 正在进行主题聚类和趋势分析，请稍候...\n\n"
        else:
            step5_progress = "🔄 Performing topic clustering and trend analysis, please wait...\n\n"
        
        for chunk in stream_message(step5_progress):
            yield chunk
        
        topics = None
        trends = None
        
        async for item in run_with_heartbeat(
            analyzer.cluster_topics,
            summaries,
            heartbeat_interval=25
        ):
            if isinstance(item, tuple) and len(item) == 2 and item[0] == "RESULT":
                topics = item[1]
                break
            else:
                yield item
        
        async for item in run_with_heartbeat(
            analyzer.analyze_trends,
            classified_papers,
            heartbeat_interval=25
        ):
            if isinstance(item, tuple) and len(item) == 2 and item[0] == "RESULT":
                trends = item[1]
                break
            else:
                yield item
        
        # 步骤6: 生成文献综述（使用心跳机制）
        for chunk in stream_message(msg_templates['step6']):
            yield chunk
        
        if language == 'zh':
            step6_progress = "🔄 正在生成文献综述，请稍候...\n\n"
        else:
            step6_progress = "🔄 Generating literature review, please wait...\n\n"
        
        for chunk in stream_message(step6_progress):
            yield chunk
        
        review = None
        async for item in run_with_heartbeat(
            generator.generate_review,
            summaries, topics or "", trends or "", query, classified_papers,
            heartbeat_interval=25
        ):
            if isinstance(item, tuple) and len(item) == 2 and item[0] == "RESULT":
                review = item[1]
                break
            else:
                yield item
        
        # 输出最终综述
        if review:
            for chunk in stream_message(msg_templates['final_title']):
                yield chunk
            for chunk in stream_message(review):
                yield chunk
        else:
            if language == 'zh':
                error_msg = "## ❌ 错误\n\n文献综述生成失败\n\n"
            else:
                error_msg = "## ❌ Error\n\nLiterature review generation failed\n\n"
            for chunk in stream_message(error_msg):
                yield chunk
        
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        if language == 'zh':
            error_msg = f"## ❌ 超时错误\n\n请求处理超过 {REQUEST_TIMEOUT} 秒，已自动终止\n\n"
        else:
            error_msg = f"## ❌ Timeout Error\n\nRequest processing exceeded {REQUEST_TIMEOUT} seconds. Automatically terminated.\n\n"
        for chunk in stream_message(error_msg):
            yield chunk
    except Exception as e:
        print(f"❌ 生成文献综述失败: {e}")
        import traceback
        print(traceback.format_exc())
        if language == 'zh':
            error_msg = f"## ❌ 错误\n\n程序执行失败: {e}\n\n"
        else:
            error_msg = f"## ❌ Error\n\nProcess execution failed: {e}\n\n"
        for chunk in stream_message(error_msg):
            yield chunk


@app.post("/literature_review")
async def generate_literature_review(request: LiteratureReviewRequest):
    """
    生成文献综述
    
    Args:
        request: 包含用户查询的请求
        
    Returns:
        StreamingResponse: SSE流式响应
    """
    try:
        return StreamingResponse(
            _generate_review_internal(request.query),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "service": "ICAIS2025-LiteratureReview API",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "ICAIS2025-LiteratureReview API",
        "version": "1.0.0",
        "health": "http://localhost:3000/health",
        "docs": "http://localhost:3000/docs",
        "literature_review": "POST /literature_review"
    }


# 优雅关闭处理
def shutdown_handler(signum, frame):
    print(f"\n⚠️ 收到终止信号 {signum}，正在关闭服务...")
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == "__main__":
    import uvicorn
    
    # 验证端口可用性
    import socket
    def check_port(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return True
            except OSError:
                return False
    
    if not check_port(3000):
        print(f"❌ 端口3000已被占用，请检查是否有其他服务在使用")
        sys.exit(1)
    
    print("🚀 启动 FastAPI 服务...")
    print(f"📍 监听地址: http://0.0.0.0:3000")
    print(f"📝 健康检查: curl http://localhost:3000/health")
    print(f"📚 API文档: http://localhost:3000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3000,
        log_level="info",
        access_log=True,
        reload=False,
        workers=1,
        loop="asyncio",
        timeout_keep_alive=30,
        limit_concurrency=100,
    )

