
# rag_prompt_builder_embeddings.py
# Build a concise LLM prompt using a target user and its neighbors.
from typing import List, Dict

def build_prompt(target_user_id: str, neighbors: List[Dict]) -> str:
    """
    neighbors: list of dicts with keys:
      - user_id
      - cosine_distance
    """
    header = "다음은 타깃 사용자와 임베딩 상 가까운 사용자들입니다.\n"
    target = f"- 타깃 사용자: {target_user_id}\n\n"
    lines = ["[Top-K 유사 사용자]"]
    for i, n in enumerate(neighbors, 1):
        cos = n.get("cosine_distance", None)
        cos_str = f"{cos:.6f}" if isinstance(cos, (int, float)) else str(cos)
        lines.append(f"{i}. {n.get('user_id')} (cosine distance={cos_str})")
    guide = (
        "\n\n위 이웃 목록을 근거로, 타깃 사용자에게 적합한 마케팅 한 줄 제안 3가지를 "
        "한국어로 제시하세요. 각 제안은 25자 이내로 간결하게."
    )
    return header + target + "\n".join(lines) + guide
