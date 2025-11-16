"""
API服务 v2 - 纯Prompt文献综述生成方案
不使用检索API，完全依赖大模型的知识库
"""
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
from review_generator_v2 import ReviewGeneratorV2
from prompt_template_v2 import detect_language


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
    title="ICAIS2025-LiteratureReview API v2",
    version="2.0.0",
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
    """内部生成器函数，执行实际的文献综述生成逻辑（v2版本）"""
    start_time = time.time()
    
    try:
        # 先检测语言，用于后续消息模板
        language = await asyncio.to_thread(detect_language, query)
        
        # 根据语言设置消息模板
        if language == 'zh':
            msg_templates = {
                'step1': "### 🔍 步骤 1/2: 查询理解与知识规划\n\n",
                'step2': "### 📝 步骤 2/2: 生成文献综述\n\n",
                'final_title': "## 📄 文献综述\n\n",
                'error_config': "## ❌ 错误\n\n配置验证失败，请检查环境变量设置\n\n",
                'error_config_exception': lambda e: f"## ❌ 错误\n\n配置验证异常: {e}\n\n",
                'error_llm_init': lambda e: f"## ❌ 错误\n\nLLM客户端初始化失败: {e}\n\n",
                'error_timeout': lambda t: f"## ❌ 超时错误\n\n请求处理超过 {t} 秒，已自动终止\n\n",
                'error_general': lambda e: f"## ❌ 错误\n\n程序执行失败: {e}\n\n"
            }
        else:
            msg_templates = {
                'step1': "### 🔍 Step 1/2: Query Understanding and Knowledge Planning\n\n",
                'step2': "### 📝 Step 2/2: Literature Review Generation\n\n",
                'final_title': "## 📄 Literature Review\n\n",
                'error_config': "## ❌ Error\n\nConfiguration validation failed. Please check environment variables.\n\n",
                'error_config_exception': lambda e: f"## ❌ Error\n\nConfiguration validation exception: {e}\n\n",
                'error_llm_init': lambda e: f"## ❌ Error\n\nLLM client initialization failed: {e}\n\n",
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
        
        generator = ReviewGeneratorV2(llm_client, language=language)
        
        # 步骤1: 查询理解与知识规划
        for chunk in stream_message(msg_templates['step1']):
            yield chunk
        
        if language == 'zh':
            step1_progress = "🔄 正在深度分析查询意图，规划知识结构...\n\n"
        else:
            step1_progress = "🔄 Deeply analyzing query intent, planning knowledge structure...\n\n"
        
        for chunk in stream_message(step1_progress):
            yield chunk
        
        knowledge_plan = None
        async for item in run_with_heartbeat(
            generator.understand_query,
            query,
            heartbeat_interval=25
        ):
            if isinstance(item, tuple) and len(item) == 2 and item[0] == "RESULT":
                knowledge_plan = item[1]
                break
            else:
                yield item
        
        if not knowledge_plan:
            if language == 'zh':
                error_msg = "## ❌ 错误\n\n查询理解失败\n\n"
            else:
                error_msg = "## ❌ Error\n\nQuery understanding failed\n\n"
            for chunk in stream_message(error_msg):
                yield chunk
            return
        
        # 步骤2: 生成文献综述
        for chunk in stream_message(msg_templates['step2']):
            yield chunk
        
        if language == 'zh':
            step2_progress = "🔄 正在生成高质量文献综述，请稍候...\n\n"
        else:
            step2_progress = "🔄 Generating high-quality literature review, please wait...\n\n"
        
        for chunk in stream_message(step2_progress):
            yield chunk
        
        review = None
        async for item in run_with_heartbeat(
            generator.generate_review,
            query, knowledge_plan,
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
        print(f"❌ 生成文献综述时发生错误: {e}")
        import traceback
        print(traceback.format_exc())
        if language == 'zh':
            error_msg = f"## ❌ 错误\n\n程序执行失败: {str(e)}\n\n"
        else:
            error_msg = f"## ❌ Error\n\nProcess execution failed: {str(e)}\n\n"
        for chunk in stream_message(error_msg):
            yield chunk
    finally:
        yield format_sse_done()


@app.post("/literature_review", response_class=StreamingResponse)
async def literature_review_endpoint(request: LiteratureReviewRequest):
    """
    文献综述生成端点（v2版本 - 纯Prompt方案）
    
    不使用检索API，完全依赖大模型的知识库生成高质量文献综述
    """
    try:
        # 使用asyncio.wait_for设置超时
        async def generate_with_timeout():
            async for chunk in _generate_review_internal(request.query):
                yield chunk
        
        return StreamingResponse(
            generate_with_timeout(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        print(f"❌ 处理请求时发生错误: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "ICAIS2025-LiteratureReview API v2", "version": "2.0.0"}


# 信号处理
def signal_handler(sig, frame):
    """处理退出信号"""
    print("\n收到退出信号，正在关闭服务...")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量读取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3000"))
    
    print(f"🚀 启动 ICAIS2025-LiteratureReview API v2 服务...")
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"📚 API文档: http://{host}:{port}/docs")
    
    uvicorn.run(
        "api_service_v2:app",
        host=host,
        port=port,
        log_level="info",
        reload=False
    )

