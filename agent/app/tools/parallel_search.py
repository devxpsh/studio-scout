import os
from parallel import Parallel

import app.genai_client  # noqa: F401 — ensures IPv4 socket preference is active


def parallel_search(query: str) -> list[dict]:
    """Searches the web for up-to-date information using the Parallel Search API.

    Use this whenever you need current facts, locations, permits, prices,
    or anything not reliably known from training data.

    Args:
        query: A concise keyword search query.

    Returns:
        A list of result objects, each with title, url, excerpt, and source.
    """
    api_key = os.environ.get("PARALLEL_API_KEY", "").strip()
    if not api_key:
        return []
    try:
        client = Parallel(api_key=api_key)
        result = client.search(
            search_queries=[query],
            mode="basic",
        )
    except Exception:
        return []

    evidence = []
    for r in result.results[:5]:
        evidence.append({
            "title": r.title,
            "url": r.url,
            "excerpt": r.excerpts[0] if r.excerpts else "",
            "source": "parallel",
        })
    return evidence