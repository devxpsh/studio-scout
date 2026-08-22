import os
from parallel import Parallel

_client = None


def _get_client() -> Parallel:
    global _client
    if _client is None:
        _client = Parallel(api_key=os.environ.get("PARALLEL_API_KEY"))
    return _client


def parallel_search(query: str) -> list[dict]:
    """Searches the web for up-to-date information using the Parallel Search API.
    
    Use this whenever you need current facts, locations, permits, prices,
    or anything not reliably known from training data.

    Args:
        query: A concise 3-6 word keyword search query.

    Returns:
        A list of result objects, each with title, url, excerpt, and source.
    """
    client = _get_client()
    result = client.search(
        search_queries=[query],
        mode="basic",
    )

    evidence = []
    for r in result.results[:5]:
        evidence.append({
            "title": r.title,
            "url": r.url,
            "excerpt": r.excerpts[0] if r.excerpts else "",
            "source": "parallel",
        })
    return evidence