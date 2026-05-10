import logging
from typing import List, Dict, Any, Optional
from services.db import execute_query, execute_query_one

logger = logging.getLogger(__name__)


def get_rankings_page(
    page: int = 1,
    per_page: int = 50,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    """Get a paginated page of players sorted by rating descending.

    If ``search`` is provided, the player's rank is computed and the page
    containing them is returned instead of page 1.
    """
    if search:
        # Find the matching player(s) to determine which page to show
        match_query = """
            SELECT p.id, p.rating
            FROM players p
            LEFT JOIN player_alt_names pan ON p.id = pan.player_id
            WHERE LOWER(p.name) LIKE LOWER(%s)
               OR LOWER(pan.alt_name) LIKE LOWER(%s)
            ORDER BY p.rating DESC
            LIMIT 1
        """
        pattern = f"%{search}%"
        match = execute_query_one(match_query, (pattern, pattern))

        if match and match.get('rating') is not None:
            # Count how many active players have a higher rating
            count_query = """
                SELECT COUNT(*) AS higher
                FROM players
                WHERE rating > %s
                  AND rating IS NOT NULL
                  AND COALESCE(total_games, 0) >= 50
                  AND last_played >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
            """
            count_result = execute_query_one(count_query, (match['rating'],))
            higher = count_result['higher'] if count_result else 0

            # Compute rank (1-based) and derive page
            rank = higher + 1
            page = max(1, (rank - 1) // per_page + 1)

    offset = (page - 1) * per_page

    # Get total count of active rated players
    total_result = execute_query_one(
        """SELECT COUNT(*) AS cnt FROM players
            WHERE rating IS NOT NULL
              AND COALESCE(total_games, 0) >= 50
              AND last_played >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)"""
    )
    total = total_result['cnt'] if total_result else 0
    total_pages = max(1, (total + per_page - 1) // per_page)

    # Fetch the page of active players
    query = """
        SELECT
            p.id AS playerid,
            p.name,
            p.country,
            p.rating,
            COALESCE(p.total_games, 0) AS total_games,
            p.last_played
        FROM players p
        WHERE p.rating IS NOT NULL
          AND COALESCE(p.total_games, 0) >= 50
          AND p.last_played >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
        ORDER BY p.rating DESC
        LIMIT %s OFFSET %s
    """
    rows = execute_query(query, (per_page, offset))

    players = []
    base_rank = offset + 1
    for i, row in enumerate(rows):
        players.append({
            'rank': base_rank + i,
            'playerid': row['playerid'],
            'name': row['name'],
            'country': row['country'],
            'rating': row['rating'],
            'total_games': row['total_games'],
            'last_played': row['last_played'].strftime('%Y-%m-%d')
                        if row.get('last_played') else None,
        })

    return {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'players': players,
    }


def get_latest_tournament() -> Optional[Dict[str, Any]]:
    """Get the name and end date of the most recent tournament."""
    query = """
        SELECT name, end_date AS date
        FROM tournaments
        ORDER BY end_date DESC
        LIMIT 1
    """
    row = execute_query_one(query)
    if not row:
        return None

    return {
        'name': row['name'],
        'date': row['date'].strftime('%Y-%m-%d')
                if row.get('date') else None,
    }
