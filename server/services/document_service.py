import os
import sys
import json
import time
import hashlib
import asyncio
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict

logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent.parent.parent / "results"
UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"
METADATA_FILE = RESULTS_DIR / "_metadata.json"

# Ensure dirs exist
RESULTS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)


# ========== Progress Tracking ==========

@dataclass
class TaskProgress:
    status: str = "pending"
    stage: str = ""
    percent: int = 0
    message: str = ""
    result: Optional[dict] = None
    error: Optional[str] = None
    waiters: list = field(default_factory=list)


class ProgressTracker:
    def __init__(self):
        self._tasks: Dict[str, TaskProgress] = {}

    def create(self, task_id: str):
        self._tasks[task_id] = TaskProgress()

    def get(self, task_id: str) -> Optional[TaskProgress]:
        return self._tasks.get(task_id)

    def update(self, task_id: str, stage: str, percent: int, message: str = ""):
        task = self._tasks.get(task_id)
        if not task:
            return
        task.stage = stage
        task.percent = percent
        task.message = message
        task.status = "processing"
        for event in task.waiters:
            event.set()

    def complete(self, task_id: str, result: dict = None):
        task = self._tasks.get(task_id)
        if not task:
            return
        task.status = "completed"
        task.percent = 100
        task.result = result
        for event in task.waiters:
            event.set()

    def fail(self, task_id: str, error: str):
        task = self._tasks.get(task_id)
        if not task:
            return
        task.status = "failed"
        task.error = error
        for event in task.waiters:
            event.set()

    async def subscribe(self, task_id: str):
        """Async generator yielding progress updates."""
        task = self._tasks.get(task_id)
        if not task:
            return

        last_percent = -1
        while task.status not in ("completed", "failed"):
            if task.percent != last_percent:
                last_percent = task.percent
                yield {
                    "stage": task.stage,
                    "percent": task.percent,
                    "message": task.message
                }
            event = asyncio.Event()
            task.waiters.append(event)
            try:
                await asyncio.wait_for(event.wait(), timeout=30)
            except asyncio.TimeoutError:
                # Send heartbeat
                yield {"stage": task.stage, "percent": task.percent, "message": "Still processing..."}
            finally:
                if event in task.waiters:
                    task.waiters.remove(event)

        # Yield final state
        if task.status == "completed":
            yield {"status": "completed", "percent": 100}
        else:
            yield {"status": "failed", "message": task.error}


progress_tracker = ProgressTracker()


# ========== Metadata Storage ==========

def generate_document_id(filename: str) -> str:
    raw = f"{filename}-{time.time()}"
    return hashlib.md5(raw.encode()).hexdigest()[:8]


def load_all_metadata() -> dict:
    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {}


def save_metadata(doc_id: str, meta: dict):
    all_meta = load_all_metadata()
    all_meta[doc_id] = meta
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_meta, f, ensure_ascii=False, indent=2)


def delete_metadata(doc_id: str):
    all_meta = load_all_metadata()
    all_meta.pop(doc_id, None)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_meta, f, ensure_ascii=False, indent=2)


# ========== PDF Processing (subprocess) ==========

async def process_pdf(file_path: str, opt_dict: dict) -> dict:
    """Run page_index_main in a separate subprocess via python -c."""
    import subprocess
    import tempfile

    print(f"[process_pdf] Starting: file={file_path}")

    # Write opt_dict to a temp file
    opt_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
    json.dump(opt_dict, opt_file, ensure_ascii=False)
    opt_file.close()

    result_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
    result_file.close()

    script = f'''
import sys, json
sys.path.insert(0, r"{Path(__file__).parent.parent.parent}")
from types import SimpleNamespace
from pageindex.page_index import page_index_main

with open(r"{opt_file.name}", "r", encoding="utf-8") as f:
    opt_dict = json.load(f)
opt = SimpleNamespace(**opt_dict)
result = page_index_main(r"{file_path}", opt)
with open(r"{result_file.name}", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("DONE")
'''

    loop = asyncio.get_running_loop()
    proc = await asyncio.create_subprocess_exec(
        sys.executable, '-c', script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    print(f"[process_pdf] Subprocess returncode={proc.returncode}")
    print(f"[process_pdf] stdout={stdout.decode('utf-8', errors='replace')[:500]}")
    if proc.returncode != 0:
        print(f"[process_pdf] stderr={stderr.decode('utf-8', errors='replace')[:1000]}")

    # Clean up opt file
    try:
        os.unlink(opt_file.name)
    except Exception:
        pass

    if proc.returncode != 0:
        error_msg = stderr.decode('utf-8', errors='replace').strip()
        logger.error(f"PDF subprocess failed: {error_msg}")
        try:
            os.unlink(result_file.name)
        except Exception:
            pass
        raise RuntimeError(f"PDF processing failed:\n{error_msg}")

    # Read result
    with open(result_file.name, "r", encoding="utf-8") as f:
        result = json.load(f)
    try:
        os.unlink(result_file.name)
    except Exception:
        pass

    return result


async def process_markdown(file_path: str, params: dict) -> dict:
    """md_to_tree is async and cooperates with our event loop."""
    from pageindex.page_index_md import md_to_tree
    result = await md_to_tree(
        md_path=file_path,
        if_thinning=params.get("if_thinning", False),
        min_token_threshold=params.get("min_token_threshold", 5000),
        if_add_node_summary=params.get("if_add_node_summary", "yes"),
        summary_token_threshold=params.get("summary_token_threshold", 200),
        model=params.get("model", "deepseek-chat"),
        if_add_doc_description=params.get("if_add_doc_description", "no"),
        if_add_node_text=params.get("if_add_node_text", "no"),
        if_add_node_id=params.get("if_add_node_id", "yes"),
    )
    return result


# ========== Smart Split Fallback ==========

async def smart_split_if_single_node(result, md_path, model):
    """When tree has only 1 node (flat docx/ppt), use LLM to intelligently
    analyze the full text and create a proper hierarchical tree structure."""
    structure = result.get("structure", [])
    if len(structure) > 1:
        return result  # Already has good structure

    print(f"[Smart Split] Only {len(structure)} node(s), triggering LLM smart split...")

    # Read the full markdown content
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"[Smart Split] Cannot read {md_path}: {e}")
        return result

    # Build the prompt — ask LLM to generate titles AND summaries together
    prompt = f"""你是一个文档结构分析专家。请仔细阅读以下文档内容，分析其逻辑结构，将其划分为一个多层级的树状索引。

要求：
1. 根据内容的逻辑关系，识别出所有章节/模块/小节
2. 生成至少 2-3 层层级结构（如：平台定位 → 核心能力 → 具体功能）
3. 每个节点必须有清晰的标题（title）和简要总结（summary）
4. summary 用 2-3 句话概括该节点涵盖的核心内容
5. 层级关系要合理，符合文档内容的逻辑

文档内容：
---
{content}
---

请只输出 JSON，格式如下（不要输出其他任何内容）：
{{
  "structure": [
    {{
      "title": "一级标题",
      "summary": "该部分的整体概述",
      "nodes": [
        {{
          "title": "二级标题",
          "summary": "该部分的核心内容概括",
          "nodes": [
            {{"title": "三级标题", "summary": "该小节的内容概括"}}
          ]
        }}
      ]
    }}
  ]
}}"""

    try:
        # Reload .env for the LLM call
        import os
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent.parent / ".env")

        from pageindex.utils import ChatGPT_API_async
        llm_response = await ChatGPT_API_async(model=model, prompt=prompt)

        if llm_response == "Error":
            print("[Smart Split] LLM call failed")
            return result

        # Extract JSON from response
        json_str = llm_response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        new_structure = json.loads(json_str)
        if "structure" not in new_structure or not new_structure["structure"]:
            print("[Smart Split] LLM response has no structure")
            return result

        # Rebuild tree with node IDs (summaries already provided by LLM)
        from pageindex.page_index_md import (
            write_node_id,
            format_structure,
        )

        tree_structure = new_structure["structure"]
        write_node_id(tree_structure)
        tree_structure = format_structure(
            tree_structure,
            order=["title", "node_id", "summary", "prefix_summary", "text", "line_num", "nodes"]
        )

        doc_description = result.get("description", "")
        new_result = {"doc_name": result.get("doc_name", ""), "structure": tree_structure}
        if doc_description:
            new_result["description"] = doc_description

        print(f"[Smart Split] Success! Tree now has {_count_nodes(tree_structure)} nodes")
        return new_result

    except Exception as e:
        print(f"[Smart Split] Error: {e}")
        return result  # fallback to original


def _count_nodes(nodes):
    count = 0
    for node in nodes:
        count += 1
        if "nodes" in node and node["nodes"]:
            count += _count_nodes(node["nodes"])
    return count


# ========== Orchestration ==========

def _get_config_values():
    """Read current config from environment variables and config.yaml."""
    print("[_get_config_values] START")
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    print(f"[_get_config_values] env_path={env_path} exists={env_path.exists()}")
    if env_path.exists():
        load_dotenv(env_path)
    import yaml
    config_path = Path(__file__).parent.parent.parent / "pageindex" / "config.yaml"
    print(f"[_get_config_values] config_path={config_path} exists={config_path.exists()}")
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    print(f"[_get_config_values] cfg={cfg}")
    return cfg


async def orchestrate_processing(document_id: str, file_path: str, file_type: str):
    """Wraps the actual processing with estimated progress stages."""
    tracker = progress_tracker
    cfg = _get_config_values()

    print(f"[Orchestrate] START doc={document_id} type={file_type} file={file_path}")
    print(f"[Orchestrate] config: model={cfg.get('model')}, api_key_set={bool(os.getenv('CHATGPT_API_KEY'))}")

    tracker.update(document_id, "uploading", 5, "File received, starting processing...")
    await asyncio.sleep(0.5)

    try:
        if file_type == "pdf":
            tracker.update(document_id, "extracting_text", 15, "Extracting text from PDF...")
            await asyncio.sleep(0.3)
            tracker.update(document_id, "analyzing_structure", 30, "Analyzing document structure with LLM...")

            opt_dict = {
                "model": cfg.get("model", "deepseek-chat"),
                "toc_check_page_num": cfg.get("toc_check_page_num", 20),
                "max_page_num_each_node": cfg.get("max_page_num_each_node", 10),
                "max_token_num_each_node": cfg.get("max_token_num_each_node", 20000),
                "if_add_node_id": cfg.get("if_add_node_id", "yes"),
                "if_add_node_summary": cfg.get("if_add_node_summary", "yes"),
                "if_add_doc_description": cfg.get("if_add_doc_description", "no"),
                "if_add_node_text": cfg.get("if_add_node_text", "no"),
            }

            print(f"[Orchestrate] Calling process_pdf...")
            result = await process_pdf(file_path, opt_dict)
            print(f"[Orchestrate] process_pdf done, result keys: {list(result.keys())}")

        elif file_type == "markdown":
            tracker.update(document_id, "parsing_markdown", 15, "Parsing Markdown structure...")
            await asyncio.sleep(0.3)
            tracker.update(document_id, "building_tree", 30, "Building tree with LLM analysis...")

            params = {
                "model": cfg.get("model", "deepseek-chat"),
                "if_thinning": cfg.get("if_thinning", False),
                "min_token_threshold": cfg.get("min_token_threshold", 5000),
                "if_add_node_summary": cfg.get("if_add_node_summary", "yes"),
                "summary_token_threshold": cfg.get("summary_token_threshold", 200),
                "if_add_doc_description": cfg.get("if_add_doc_description", "no"),
                "if_add_node_text": cfg.get("if_add_node_text", "no"),
                "if_add_node_id": cfg.get("if_add_node_id", "yes"),
            }

            result = await process_markdown(file_path, params)

            # Fallback: if tree has only 1 node, use LLM smart split
            result = await smart_split_if_single_node(result, file_path, cfg.get("model", "deepseek-chat"))

        else:
            # txt, json, csv, word → convert to Markdown first, then process
            from server.services.converter_service import convert_to_markdown

            type_labels = {
                "text": "TXT",
                "json": "JSON",
                "csv": "CSV",
                "word": "Word",
            }
            label = type_labels.get(file_type, file_type.upper())

            tracker.update(document_id, "converting", 10,
                           f"Converting {label} to Markdown...")
            await asyncio.sleep(0.3)

            # Convert to markdown
            md_path = str(UPLOADS_DIR / f"{document_id}_converted.md")
            convert_to_markdown(file_path, md_path, file_type)

            tracker.update(document_id, "parsing_markdown", 25,
                           f"Parsing converted Markdown structure...")
            await asyncio.sleep(0.3)
            tracker.update(document_id, "building_tree", 40,
                           "Building tree with LLM analysis...")

            params = {
                "model": cfg.get("model", "deepseek-chat"),
                "if_thinning": cfg.get("if_thinning", False),
                "min_token_threshold": cfg.get("min_token_threshold", 5000),
                "if_add_node_summary": cfg.get("if_add_node_summary", "yes"),
                "summary_token_threshold": cfg.get("summary_token_threshold", 200),
                "if_add_doc_description": cfg.get("if_add_doc_description", "no"),
                "if_add_node_text": cfg.get("if_add_node_text", "no"),
                "if_add_node_id": cfg.get("if_add_node_id", "yes"),
            }

            result = await process_markdown(md_path, params)

            # Fallback: if tree has only 1 node, use LLM smart split
            result = await smart_split_if_single_node(result, md_path, cfg.get("model", "deepseek-chat"))

            # Clean up converted file
            try:
                os.unlink(md_path)
            except Exception:
                pass

        tracker.update(document_id, "saving", 90, "Saving results...")
        await asyncio.sleep(0.2)

        # Save result
        output_path = RESULTS_DIR / f"{document_id}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # Update metadata
        meta = load_all_metadata().get(document_id, {})
        meta["status"] = "completed"
        save_metadata(document_id, meta)

        tracker.complete(document_id, result)

    except Exception as e:
        print(f"[Orchestrate] FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        meta = load_all_metadata().get(document_id, {})
        meta["status"] = "failed"
        meta["error"] = str(e)
        save_metadata(document_id, meta)
        tracker.fail(document_id, str(e))
