import os
import json
import csv
import io
import asyncio
import time
import html as html_lib
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, FileResponse

from server.services.document_service import (
    generate_document_id, save_metadata, load_all_metadata, delete_metadata,
    progress_tracker, orchestrate_processing, RESULTS_DIR, UPLOADS_DIR,
)
from server.services.tree_service import load_tree, get_skeleton, get_node_by_id, count_all_nodes
from server.services.converter_service import get_file_type, SUPPORTED_EXTENSIONS

# MIME types for source file serving
SOURCE_MIME_TYPES = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.md': 'text/markdown',
    '.txt': 'text/plain',
    '.json': 'application/json',
    '.csv': 'text/csv',
}


def _resolve_source_path(document_id: str, meta: dict) -> Path | None:
    """Resolve the actual file path for a document."""
    stored_path = meta.get("file_path", "")
    filename = meta.get("filename", "unknown")
    ext = os.path.splitext(filename)[1].lower()

    # Try the stored path
    if stored_path and Path(stored_path).exists():
        return Path(stored_path)
    # Fallback: uploads dir by doc_id + extension
    candidate = UPLOADS_DIR / f"{document_id}{ext}"
    if candidate.exists():
        return candidate
    # Try all files in uploads that match doc_id prefix
    for f in UPLOADS_DIR.iterdir():
        if f.name.startswith(document_id):
            return f
    return None

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document and begin tree generation.
    Supports: PDF, Markdown, TXT, JSON, CSV, Word (docx).
    """
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()

    supported_exts = list(SUPPORTED_EXTENSIONS.keys())
    file_type = get_file_type(ext)
    if not file_type:
        supported_str = ", ".join(supported_exts)
        raise HTTPException(400, f"Unsupported file type: {ext}. Supported: {supported_str}")

    # Read file content
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(400, "File too large. Maximum size is 50MB.")

    # Generate ID and save file
    doc_id = generate_document_id(filename)
    file_path = UPLOADS_DIR / f"{doc_id}{ext}"
    with open(file_path, "wb") as f:
        f.write(content)

    # Save metadata
    meta = {
        "document_id": doc_id,
        "filename": filename,
        "file_type": file_type,
        "status": "processing",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "file_path": str(file_path),
    }
    save_metadata(doc_id, meta)

    # Create progress tracker and start background task
    progress_tracker.create(doc_id)
    asyncio.create_task(orchestrate_processing(doc_id, str(file_path), file_type))

    return {
        "document_id": doc_id,
        "filename": filename,
        "file_type": file_type,
        "status": "processing",
        "created_at": meta["created_at"],
    }


@router.get("")
async def list_documents():
    """List all documents."""
    all_meta = load_all_metadata()
    documents = []
    for doc_id, meta in all_meta.items():
        status = meta.get("status", "unknown")

        # Auto-fix: if status says "processing" but tree file exists, mark as completed
        if status == "processing":
            tree_path = RESULTS_DIR / f"{doc_id}.json"
            if tree_path.exists():
                status = "completed"
                meta["status"] = "completed"
                save_metadata(doc_id, meta)

        doc_info = {
            "document_id": doc_id,
            "filename": meta.get("filename", "unknown"),
            "file_type": meta.get("file_type", "unknown"),
            "status": status,
            "created_at": meta.get("created_at", ""),
        }
        # If completed, count nodes
        if meta.get("status") == "completed":
            try:
                tree = load_tree(doc_id)
                doc_info["node_count"] = count_all_nodes(tree)
            except Exception:
                doc_info["node_count"] = 0
        documents.append(doc_info)

    # Sort by created_at descending
    documents.sort(key=lambda d: d.get("created_at", ""), reverse=True)
    return {"documents": documents}


@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get document metadata."""
    all_meta = load_all_metadata()
    meta = all_meta.get(document_id)
    if not meta:
        raise HTTPException(404, f"Document not found: {document_id}")
    return meta


@router.get("/{document_id}/tree")
async def get_document_tree(document_id: str):
    """Get the full generated tree structure."""
    try:
        tree = load_tree(document_id)
        return tree
    except FileNotFoundError:
        raise HTTPException(404, f"Tree not found for document: {document_id}")


@router.get("/{document_id}/tree/skeleton")
async def get_document_tree_skeleton(document_id: str):
    """Get tree without text fields."""
    try:
        tree = load_tree(document_id)
        return get_skeleton(tree)
    except FileNotFoundError:
        raise HTTPException(404, f"Tree not found for document: {document_id}")


@router.get("/{document_id}/nodes/{node_id}")
async def get_node(document_id: str, node_id: str):
    """Get a single node's full data."""
    try:
        tree = load_tree(document_id)
        node = get_node_by_id(tree, node_id)
        if not node:
            raise HTTPException(404, f"Node not found: {node_id}")
        return node
    except FileNotFoundError:
        raise HTTPException(404, f"Tree not found for document: {document_id}")


@router.get("/{document_id}/progress")
async def get_progress(document_id: str):
    """SSE endpoint — streams processing progress events."""
    all_meta = load_all_metadata()
    meta = all_meta.get(document_id)
    if not meta:
        raise HTTPException(404, f"Document not found: {document_id}")

    # If already completed, return immediately
    if meta.get("status") == "completed":
        async def done_stream():
            yield f'data: {json.dumps({"status": "completed", "percent": 100})}\n\n'
        return StreamingResponse(done_stream(), media_type="text/event-stream")

    # If failed, return the error
    if meta.get("status") == "failed":
        async def fail_stream():
            yield f'data: {json.dumps({"status": "failed", "message": meta.get("error", "Processing failed")})}\n\n'
        return StreamingResponse(fail_stream(), media_type="text/event-stream")

    # If "processing" but no active task (server restarted), re-trigger processing
    task = progress_tracker.get(document_id)
    if not task:
        file_path = meta.get("file_path", "")
        file_type = meta.get("file_type", "pdf")
        if file_path and Path(file_path).exists():
            progress_tracker.create(document_id)
            asyncio.create_task(orchestrate_processing(document_id, file_path, file_type))
        else:
            async def no_file_stream():
                yield f'data: {json.dumps({"status": "failed", "message": "Source file not found, please re-upload"})}\n\n'
            return StreamingResponse(no_file_stream(), media_type="text/event-stream")

    async def event_stream():
        async for update in progress_tracker.subscribe(document_id):
            yield f"data: {json.dumps(update, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its generated tree."""
    # Delete tree file
    tree_path = RESULTS_DIR / f"{document_id}.json"
    if tree_path.exists():
        tree_path.unlink()

    # Delete uploaded file
    all_meta = load_all_metadata()
    meta = all_meta.get(document_id, {})
    file_path = meta.get("file_path")
    if file_path and Path(file_path).exists():
        Path(file_path).unlink()

    # Delete metadata
    delete_metadata(document_id)

    return {"status": "deleted"}


@router.get("/{document_id}/source")
async def get_source_file(document_id: str):
    """Download the original source file. Used by the source viewer panel."""
    all_meta = load_all_metadata()
    meta = all_meta.get(document_id)
    if not meta:
        raise HTTPException(404, f"Document not found: {document_id}")

    file_path = _resolve_source_path(document_id, meta)
    if not file_path or not file_path.exists():
        raise HTTPException(404, "Source file not found")

    filename = meta.get("filename", "unknown")
    ext = os.path.splitext(filename)[1].lower()
    media_type = SOURCE_MIME_TYPES.get(ext, "application/octet-stream")
    return FileResponse(
        str(file_path),
        media_type=media_type,
        filename=filename,
    )


@router.get("/{document_id}/source-info")
async def get_source_info(document_id: str):
    """Get source file info (type, page range support) without downloading."""
    all_meta = load_all_metadata()
    meta = all_meta.get(document_id)
    if not meta:
        raise HTTPException(404, f"Document not found: {document_id}")

    filename = meta.get("filename", "unknown")
    ext = os.path.splitext(filename)[1].lower()
    file_type = meta.get("file_type", "unknown")

    # PDF supports native page navigation via browser built-in viewer
    supports_page_nav = ext == ".pdf"

    return {
        "filename": filename,
        "file_type": file_type,
        "extension": ext,
        "supports_page_navigation": supports_page_nav,
    }


@router.get("/{document_id}/source/content")
async def get_source_content(document_id: str):
    """Get parsed content of the source file for frontend rendering.
    
    Returns different formats based on file type:
    - PDF: {content_type: "pdf"} → frontend uses /source endpoint directly
    - DOCX: {content_type: "html", html: "<html>", total_paragraphs: N, tables: N}
    - TXT/MD: {content_type: "text", text: "...", total_lines: N}
    - JSON: {content_type: "json", text: "...", total_lines: N}
    - CSV: {content_type: "csv", headers: [...], rows: [[...]], total_rows: N}
    """
    all_meta = load_all_metadata()
    meta = all_meta.get(document_id)
    if not meta:
        raise HTTPException(404, f"Document not found: {document_id}")

    file_path = _resolve_source_path(document_id, meta)
    if not file_path or not file_path.exists():
        raise HTTPException(404, "Source file not found")

    filename = meta.get("filename", "unknown")
    ext = os.path.splitext(filename)[1].lower()

    try:
        if ext == ".pdf":
            return {
                "content_type": "pdf",
                "filename": filename,
                "total_pages": meta.get("total_pages"),
            }

        elif ext == ".docx":
            import docx as python_docx
            doc = python_docx.Document(str(file_path))
            html_parts = []
            table_count = 0
            para_count = 0

            for element in doc.element.body:
                tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag

                if tag == 'p':
                    para_id = element.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}paraId', '')
                    # Get text from this paragraph
                    texts = []
                    for t in element.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                        texts.append(t.text)
                    text = ''.join(texts)
                    if text.strip():
                        para_count += 1
                        # Check if it looks like a heading (bold, large, etc.)
                        is_heading = False
                        for r in element.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r'):
                            for props in r.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr'):
                                for child in props:
                                    child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                                    if child_tag == 'b':
                                        is_heading = True
                        if is_heading:
                            html_parts.append(f'<h4 class="docx-heading">{html_lib.escape(text)}</h4>')
                        else:
                            html_parts.append(f'<p>{html_lib.escape(text)}</p>')

                elif tag == 'tbl':
                    table_count += 1
                    # Extract table as HTML
                    rows = element.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr')
                    html_parts.append('<table class="docx-table">')
                    for i, row in enumerate(rows):
                        cells = row.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
                        # Get cell texts
                        cell_texts = []
                        for cell_elem in row.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc'):
                            tc_texts = cell_elem.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
                            cell_texts.append(''.join(t.text or '' for t in tc_texts))
                        if not cell_texts:
                            continue
                        tag_name = 'th' if i == 0 else 'td'
                        cells_html = ''.join(f'<{tag_name}>{html_lib.escape(ct)}</{tag_name}>' for ct in cell_texts)
                        html_parts.append(f'<tr>{cells_html}</tr>')
                    html_parts.append('</table>')

            return {
                "content_type": "html",
                "html": ''.join(html_parts),
                "total_paragraphs": para_count,
                "total_tables": table_count,
            }

        elif ext in (".txt", ".md"):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            lines = text.split('\n')
            return {
                "content_type": "text",
                "text": text,
                "total_lines": len(lines),
            }

        elif ext == ".json":
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            pretty = json.dumps(data, indent=2, ensure_ascii=False)
            lines = pretty.split('\n')
            return {
                "content_type": "json",
                "text": pretty,
                "total_lines": len(lines),
            }

        elif ext == ".csv":
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            headers = rows[0] if rows else []
            data_rows = rows[1:] if len(rows) > 1 else []
            return {
                "content_type": "csv",
                "headers": headers,
                "rows": data_rows,
                "total_rows": len(data_rows),
            }

        else:
            # Fallback: try as text
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                return {
                    "content_type": "text",
                    "text": text,
                    "total_lines": len(text.split('\n')),
                }
            except Exception:
                raise HTTPException(400, f"Unsupported file type: {ext}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to parse content: {str(e)}")
