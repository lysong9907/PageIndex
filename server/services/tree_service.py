import json
import copy
from pathlib import Path

RESULTS_DIR = Path(__file__).parent.parent.parent / "results"


def load_tree(document_id: str) -> dict:
    """Load the full tree JSON from results/."""
    # Try document_id.json first, then fallback to filename-based pattern
    tree_path = RESULTS_DIR / f"{document_id}.json"
    if not tree_path.exists():
        # Search by matching pattern in metadata
        tree_path = RESULTS_DIR / f"{document_id}_structure.json"
    if not tree_path.exists():
        raise FileNotFoundError(f"Tree not found for document: {document_id}")
    with open(tree_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_skeleton(tree: dict) -> dict:
    """Return tree with 'text' fields stripped (recursive)."""
    def strip_text(node):
        result = {k: v for k, v in node.items() if k != "text"}
        if "nodes" in result:
            result["nodes"] = [strip_text(child) for child in result["nodes"]]
        return result

    return {
        "doc_name": tree.get("doc_name", ""),
        "structure": [strip_text(n) for n in tree.get("structure", [])]
    }


def find_nodes_by_ids(tree: dict, node_ids: list) -> list:
    """Find nodes by their IDs, including their text content."""
    results = []
    target_ids = set(node_ids)

    def walk(node):
        if node.get("node_id") in target_ids:
            results.append(node)
        for child in node.get("nodes", []):
            walk(child)

    for top_node in tree.get("structure", []):
        walk(top_node)

    return results


def get_node_by_id(tree: dict, node_id: str) -> dict | None:
    """Get a single node by its ID."""
    nodes = find_nodes_by_ids(tree, [node_id])
    return nodes[0] if nodes else None


def count_all_nodes(tree: dict) -> int:
    """Count total number of nodes in the tree."""
    count = 0

    def walk(node):
        nonlocal count
        count += 1
        for child in node.get("nodes", []):
            walk(child)

    for top_node in tree.get("structure", []):
        walk(top_node)

    return count
