import os
import json
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from dotenv import load_dotenv, set_key
import yaml

router = APIRouter(prefix="/api/config", tags=["config"])

PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
CONFIG_YAML_PATH = PROJECT_ROOT / "pageindex" / "config.yaml"


def _load_env():
    load_dotenv(ENV_PATH, override=True)


def _read_config_yaml():
    with open(CONFIG_YAML_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _write_config_yaml(data: dict):
    with open(CONFIG_YAML_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


@router.get("")
async def get_config():
    """Get current LLM and processing configuration."""
    _load_env()
    cfg = _read_config_yaml()

    api_key = os.getenv("CHATGPT_API_KEY", "")
    api_key_preview = f"...{api_key[-4:]}" if len(api_key) > 4 else ""

    return {
        "llm": {
            "model": cfg.get("model", "deepseek-chat"),
            "api_base_url": os.getenv("API_BASE_URL", "https://api.deepseek.com"),
            "api_key_set": bool(api_key),
            "api_key_preview": api_key_preview,
        },
        "processing": {
            "toc_check_page_num": cfg.get("toc_check_page_num", 20),
            "max_page_num_each_node": cfg.get("max_page_num_each_node", 10),
            "max_token_num_each_node": cfg.get("max_token_num_each_node", 20000),
            "if_add_node_id": cfg.get("if_add_node_id", "yes"),
            "if_add_node_summary": cfg.get("if_add_node_summary", "yes"),
            "if_add_doc_description": cfg.get("if_add_doc_description", "no"),
            "if_add_node_text": cfg.get("if_add_node_text", "no"),
        }
    }


@router.patch("")
async def update_config(request: Request):
    """Update configuration (partial update)."""
    body = await request.json()

    # Update LLM settings
    llm = body.get("llm", {})
    if "api_key" in llm and llm["api_key"]:
        set_key(str(ENV_PATH), "CHATGPT_API_KEY", llm["api_key"])
    if "api_base_url" in llm:
        set_key(str(ENV_PATH), "API_BASE_URL", llm["api_base_url"])

    # Update config.yaml
    cfg = _read_config_yaml()
    if "model" in llm:
        cfg["model"] = llm["model"]

    processing = body.get("processing", {})
    for key in ["toc_check_page_num", "max_page_num_each_node", "max_token_num_each_node",
                "if_add_node_id", "if_add_node_summary", "if_add_doc_description", "if_add_node_text"]:
        if key in processing:
            cfg[key] = processing[key]

    _write_config_yaml(cfg)

    # Reload env
    _load_env()

    return await get_config()


@router.post("/test-connection")
async def test_connection(request: Request):
    """Test the LLM API connection."""
    body = await request.json()

    api_key = body.get("api_key", os.getenv("CHATGPT_API_KEY", ""))
    base_url = body.get("api_base_url", os.getenv("API_BASE_URL", "https://api.deepseek.com"))
    model = body.get("model", "deepseek-chat")

    if not api_key:
        return {"success": False, "error": "API key is not set"}

    try:
        from openai import AsyncOpenAI
        import time

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        start = time.time()
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello, respond with just 'OK'."}],
            max_tokens=10,
        )
        latency = int((time.time() - start) * 1000)

        return {
            "success": True,
            "latency_ms": latency,
            "model_name": model,
            "response": response.choices[0].message.content,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
