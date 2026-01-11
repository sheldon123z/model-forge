"""
Model Forge Server - FastAPI 服务入口
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router

# 创建 FastAPI 应用
app = FastAPI(
    title="Model Forge",
    description="3D模型生成服务 - 从需求描述到3D模型的完整流水线",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 注册 API 路由
app.include_router(api_router)


# 主页 - 返回前端界面
@app.get("/", response_class=HTMLResponse)
async def index():
    """返回前端界面"""
    template_path = Path(__file__).parent.parent / "templates" / "index.html"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return """
    <html>
        <head><title>Model Forge</title></head>
        <body>
            <h1>Model Forge - 3D模型生成服务</h1>
            <p>API 文档: <a href="/docs">/docs</a></p>
        </body>
    </html>
    """


def run_server(host: str = "0.0.0.0", port: int = 8088, reload: bool = False):
    """运行服务器"""
    import uvicorn
    uvicorn.run(
        "model_forge.server:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8088))
    run_server(port=port)
