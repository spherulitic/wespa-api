import logging
from typing import List, Optional, Dict, Any
from services.db import execute_query, execute_query_one

logger = logging.getLogger(__name__)


def get_tournament_v2(tourney_id: int) -> Optional[Dict[str, Any]]:
    """Get tournament-level info: name, date, location.

    The tournament id in the DB is the `tournaments.id` column.
    Location comes from the associated event (events.location, events.country).
    Date is the tournament start_date.
    """
    query = """
        SELECT
            t.id as tourneyid,
            t.name,
            t.start_date as date,
            CONCAT(COALESCE(e.location, ''), ', ', COALESCE(e.country, e.country, '')) as location
        FROM tournaments t
        LEFT JOIN events e ON t.event_id = e.id
        WHERE t.id = %s
    """
    return execute_query_one(query, (tourney_id,))


def get_divisions_for_tournament(tourney_id: int) -> List[Dict[str, Any]]:
    """Get all divisions belonging to a tournament."""
    query = """
        SELECT
            d.id as division_id,
            d.name,
            d.number as division_number
        FROM divisions d
        WHERE d.tournament_id = %s
        ORDER BY d.number ASC
    """
    return execute_query(query, (tourney_id,))


def get_standings_for_division(division_id: int) -> List[Dict[str, Any]]:
    """Get all player standings for a given division, ordered by position.

    Uses the tournament_results table joined with players for name/country.
    """
    query = """
        SELECT
            tr.position as place,
            p.id as playerid,
            p.name,
            p.country,
            tr.wins,
            tr.losses,
            COALESCE(tr.byes, 0) as byes,
            COALESCE(tr.spread, 0) as spread,
            tr.start_rating,
            tr.end_rating,
            (COALESCE(tr.end_rating, 0) - COALESCE(tr.start_rating, 0)) as rating_change,
            tr.old_rating_dev as start_deviation,
            tr.new_rating_dev as end_deviation
        FROM tournament_results tr
        JOIN players p ON tr.player_id = p.id
        WHERE tr.division_id = %s
        ORDER BY tr.position ASC
    """
    return execute_query(query, (division_id,))
