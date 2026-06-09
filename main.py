# -*- coding: utf-8 -*-
"""Bid Workbench API — FastAPI backend."""
from dotenv import load_dotenv
import os
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_BASE_DIR, ".env"))


import shutil
import asyncio
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.task_manager import Task, ensure_dirs
from services.doc_parser import parse_file
from services.tech_extractor import extract_requirements, expand_requirements, adjust_business_and_pricing
from services.docx_builder import build_final_docx

# --- App Setup ---
app = FastAPI(title="Bid Workbench", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_dirs()

TEMPLATE_PATH = os.environ.get(
    "TEMPLATE_PATH",
    os.path.join(_BASE_DIR, "template", "商务+报价.docx")
)


# --- Models ---
class ExtractRequest(BaseModel):
    task_id: str


class ExpandRequest(BaseModel):
    task_id: str
    confirmed_requirements: list


class AdjustRequest(BaseModel):
    task_id: str


class GenerateRequest(BaseModel):
    task_id: str


# --- API Routes ---
@app.get("/api/health")
def health():
    return {"service": "Bid Workbench API", "version": "1.0.0", "status": "ok"}


@app.post("/api/upload")
async def upload_tender(file: UploadFile = File(...)):
    """Upload a tender document, parse it, and create a task."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    task = Task()
    ext = Path(file.filename).suffix
    save_path = os.path.join(task.upload_dir, f"tender{ext}")

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    task.tender_file_path = save_path
    task.tender_text = parse_file(save_path, file.filename)
    task.project_name = "待提取"
    task.status = "UPLOADED"
    task.save()

    return {
        "task_id": task.task_id,
        "project_name": task.project_name,
        "status": task.status,
        "message": f"文件 '{file.filename}' 上传成功，共 {len(task.tender_text)} 字符",
    }


@app.post("/api/extract")
async def extract_tech_requirements(req: ExtractRequest):
    """Extract technical requirements from uploaded tender document."""
    task = Task.load(req.task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    task.update_status("EXTRACTING")

    try:
        result = await extract_requirements(task.tender_text)
        task.requirements = result.get("requirements", [])
        task.project_name = result.get("project_name", "未命名项目")
        task.status = "PENDING_REVIEW"
        task.save()

        return {
            "task_id": task.task_id,
            "project_name": task.project_name,
            "requirements": task.requirements,
            "status": task.status,
            "message": f"已提取 {len(task.requirements)} 条技术要求，请审核确认",
        }
    except Exception as e:
        task.update_status("ERROR")
        task.error = str(e)
        task.save()
        raise HTTPException(500, f"提取失败: {e}")


@app.post("/api/expand")
async def expand_tech_solution(req: ExpandRequest):
    """Expand confirmed technical requirements into detailed solutions (SSE streaming)."""
    task = Task.load(req.task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    task.requirements = req.confirmed_requirements
    task.update_status("EXPANDING")

    async def event_stream():
        try:
            full_content = ""
            async for chunk in expand_requirements_stream(
                task.requirements, task.project_name
            ):
                full_content += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            task.expanded_solution = full_content
            task.status = "TECH_REVIEW"
            task.save()

            yield f"data: {json.dumps({'type': 'done', 'task_id': task.task_id, 'status': 'TECH_REVIEW'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            task.update_status("ERROR")
            task.error = str(e)
            task.save()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.post("/api/adjust")
async def adjust_business_pricing(req: AdjustRequest):
    """LLM adjusts business and pricing sections based on tender doc."""
    task = Task.load(req.task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    task.update_status("ADJUSTING")

    try:
        # Read template content for reference
        from services.doc_parser import parse_docx
        template_text = parse_docx(TEMPLATE_PATH) if os.path.exists(TEMPLATE_PATH) else ""

        adjusted = await adjust_business_and_pricing(
            template_text, task.tender_text, task.project_name
        )

        task.status = "GENERATING"
        task.save()

        return {
            "task_id": task.task_id,
            "status": task.status,
            "message": "商务+报价内容已根据招标文件智能调整",
            "preview": adjusted[:500] + "..." if len(adjusted) > 500 else adjusted,
        }
    except Exception as e:
        task.update_status("ERROR")
        task.error = str(e)
        task.save()
        raise HTTPException(500, f"调整失败: {e}")


@app.post("/api/generate")
async def generate_docx(req: GenerateRequest):
    """Build the final Word document with all three sections."""
    task = Task.load(req.task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    task.update_status("GENERATING")

    try:
        output_filename = f"【新】{task.project_name}完整投标文件.docx"
        output_path = os.path.join(task.output_dir, output_filename)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            build_final_docx,
            task.expanded_solution,
            task.project_name,
            output_path,
            TEMPLATE_PATH,
        )

        task.output_path = output_path
        task.status = "COMPLETED"
        task.save()

        return {
            "task_id": task.task_id,
            "status": task.status,
            "filename": output_filename,
            "message": "投标文件生成完毕！",
        }
    except Exception as e:
        task.update_status("ERROR")
        task.error = str(e)
        task.save()
        raise HTTPException(500, f"生成失败: {e}")


@app.get("/api/download/{task_id}")
async def download_docx(task_id: str):
    """Download the generated Word file."""
    task = Task.load(task_id)
    if not task or task.status != "COMPLETED":
        raise HTTPException(404, "Task not found or not completed")

    if not os.path.exists(task.output_path):
        raise HTTPException(404, "Output file not found")

    return FileResponse(
        task.output_path,
        filename=os.path.basename(task.output_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """Query task status."""
    task = Task.load(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    return {
        "task_id": task.task_id,
        "status": task.status,
        "project_name": task.project_name,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "error": task.error,
    }


@app.get("/api/tasks")
async def list_tasks():
    """List all tasks."""
    from services.task_manager import TASKS_DIR
    tasks = []
    if os.path.exists(TASKS_DIR):
        for fname in os.listdir(TASKS_DIR):
            if fname.endswith(".json"):
                task_id = fname.replace(".json", "")
                t = Task.load(task_id)
                if t:
                    tasks.append({
                        "task_id": t.task_id,
                        "status": t.status,
                        "project_name": t.project_name,
                        "created_at": t.created_at,
                    })
    tasks.sort(key=lambda x: x["created_at"], reverse=True)
    return {"tasks": tasks}


# --- Helper: streaming expansion ---
async def expand_requirements_stream(requirements, project_name):
    """Stream expansion results from LLM."""
    from services.llm_service import llm_service
    from services.tech_extractor import EXPAND_SYSTEM_PROMPT

    user_content = f"项目名称：{project_name}\n\n需要扩充的{len(requirements)}条技术要求：\n\n"
    for req in requirements:
        user_content += f"{req['id']}. 【{req.get('source', '')}】{req['text']}\n\n"

    messages = [{"role": "user", "content": user_content}]
    async for chunk in llm_service.chat_stream(messages, EXPAND_SYSTEM_PROMPT):
        yield chunk


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


# --- Serve Frontend Static Files (must be LAST) ---
# This serves the React build output from ./static directory.
# Any non-API path falls back to index.html (SPA routing).
_STATIC_DIR = os.path.join(_BASE_DIR, "static")

if os.path.isdir(_STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(_STATIC_DIR, "assets")), name="assets")

    @app.get("/")
    @app.head("/")
    async def serve_root():
        """Explicitly serve index.html for root path."""
        index = os.path.join(_STATIC_DIR, "index.html")
        if os.path.exists(index):
            return FileResponse(index)
        return {"error": "Frontend not built yet"}

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Catch-all: serve index.html for any non-API route (SPA support)."""
        # Skip API paths (shouldn't reach here, but safety net)
        if full_path.startswith("api/") or full_path.startswith("api"):
            raise HTTPException(404, "Not found")
        index = os.path.join(_STATIC_DIR, "index.html")
        if os.path.exists(index):
            return FileResponse(index)
        return {"error": "Frontend not built yet. Run: cd frontend && npm run build"}
