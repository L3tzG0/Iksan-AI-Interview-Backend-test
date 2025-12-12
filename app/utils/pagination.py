from typing import Callable, Tuple, List, Any
from postgrest.exceptions import APIError

# Type alias for a callable that returns a fresh Postgrest query builder
QueryFactory = Callable[[], Any]

async def paginate_query(
    query_factory: QueryFactory,
    skip: int,
    limit: int,
) -> Tuple[List[dict], int]:
    """Execute a paginated Supabase query with consistent 416 handling.

    `query_factory` must return a new query builder each time so we avoid
    in-place mutation side effects from offset/limit calls.
    """
    paginated_query = query_factory().offset(skip).limit(limit)
    try:
        response = await paginated_query.execute()
        total = response.count if response.count is not None else 0
        return response.data or [], total
    except APIError as exc:
        if exc.code in ("416", 416):
            count_response = await query_factory().limit(0).execute()
            total = count_response.count if count_response.count is not None else 0
            return [], total
        raise
