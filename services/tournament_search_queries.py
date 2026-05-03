import logging
from typing import List, Dict, Any
from services.db import execute_query

logger = logging.getLogger(__name__)


def search_tournaments(
    q: str = None,
    country: str = None,
    from_date: str = None,
    to_date: str = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """Search tournaments by name, country, and/or date range.

    All filters are optional; at least one is expected to be provided
    by the caller.
    """
    conditions = []
    params = []

    if q:
        conditions.append("t.name LIKE %s")
        params.append(f"%{q}%")

    if country:
        conditions.append("t.country = %s")
        params.append(country.upper())

    if from_date:
        conditions.append("t.start_date >= %s")
        params.append(from_date)

    if to_date:
        conditions.append("t.start_date <= %s")
        params.append(to_date)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = f"""
        SELECT
            t.id as tourneyid,
            t.name,
            t.start_date,
            t.end_date,
            t.country,
            e.location
        FROM tournaments t
        LEFT JOIN events e ON t.event_id = e.id
        WHERE {where_clause}
        ORDER BY t.start_date DESC, t.name ASC
        LIMIT %s
    """
    params.append(limit)

    return execute_query(query, tuple(params))
