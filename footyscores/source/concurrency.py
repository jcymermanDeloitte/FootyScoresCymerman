from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, List


def map_with_concurrency(
    items: List[str],
    concurrency: int,
    mapper: Callable[[str], Any],
) -> List[Any]:
    if concurrency <= 0:
        raise ValueError("concurrency must be a positive integer.")
    if not items:
        return []

    workers = min(concurrency, len(items))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(mapper, items))
