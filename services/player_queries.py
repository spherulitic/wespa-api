import logging
from typing import List, Optional, Dict, Any
from services.db import execute_query, execute_query_one
from models.schemas import CrossTablesPlayer, TournamentResult

logger = logging.getLogger(__name__)

def get_basic_player(player_id: int) -> Optional[Dict[str, Any]]:
    """Get basic player information from players table"""
    query = """
        SELECT 
            p.id as playerid,
            p.name,
            p.rating as cswrating,
            p.country,
            p.photo as photourl,
            COALESCE(
                (SELECT rating FROM tournament_results 
                 WHERE player_id = p.id 
                 ORDER BY date DESC LIMIT 1),
                p.rating
            ) as current_rating
        FROM players p
        WHERE p.id = %s
    """
    return execute_query_one(query, (player_id,))

def get_player_career_totals(player_id: int) -> Dict[str, int]:
    """Get career wins, losses, ties, byes"""
    query = """
        SELECT 
            SUM(CASE WHEN result = 1 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN result = -1 THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN result = 0 AND score > 0 THEN 1 ELSE 0 END) as ties,
            SUM(CASE WHEN result = 0 AND score = 0 THEN 1 ELSE 0 END) as byes
        FROM player_results
        WHERE player_id = %s
    """
    result = execute_query_one(query, (player_id,))
    return {
        'wins': result.get('wins', 0) if result else 0,
        'losses': result.get('losses', 0) if result else 0,
        'ties': result.get('ties', 0) if result else 0,
        'byes': result.get('byes', 0) if result else 0
    }

def get_player_ranking(player_id: int) -> Optional[int]:
    """Get player's current world ranking based on rating"""
    query = """
        SELECT COUNT(*) + 1 as ranking
        FROM players
        WHERE rating > (SELECT rating FROM players WHERE id = %s)
        AND rating IS NOT NULL
    """
    result = execute_query_one(query, (player_id,))
    return result.get('ranking') if result else None

def get_tournament_history(player_id: int, limit: int = 20) -> List[TournamentResult]:
    """Get recent tournament results for a player"""
    query = """
        SELECT
            tr.id as tourneyid,
            tr.tournament_name as name,
            tr.date,
            d.name as division,
            tr.wins,
            tr.losses,
            tr.byes as ties,
            tr.position as place,
            (SELECT COUNT(*) FROM tournament_results tr2
             WHERE tr2.division_id = tr.division_id) as totalplayers,
            tr.start_rating as rating,
            (tr.end_rating - tr.start_rating) as ratingchange,
            COALESCE(tr.spread, 0) as points,
            (SELECT COALESCE(AVG(pr.score), 0)
             FROM games g
             JOIN player_results pr ON g.id = pr.game_id
                 AND pr.player_id = tr.player_id
                 AND pr.score > 0
             WHERE g.division_id = tr.division_id) as averagepoints
        FROM tournament_results tr
        JOIN divisions d ON tr.division_id = d.id
        WHERE tr.player_id = %s
        ORDER BY tr.date DESC
        LIMIT %s
    """
    results = execute_query(query, (player_id, limit))
    return [TournamentResult(r) for r in results]

def search_players(search_term: str, limit: int = 200) -> List[Dict[str, Any]]:
    """Search players by name (partial, case-insensitive)"""
    # Search in players table and player_alt_names
    query = """
        SELECT DISTINCT
            p.id as playerid,
            p.name,
            p.rating as cswrating,
            p.country,
            p.photo as photourl
        FROM players p
        LEFT JOIN player_alt_names pan ON p.id = pan.player_id
        WHERE LOWER(p.name) LIKE LOWER(%s) 
           OR LOWER(pan.alt_name) LIKE LOWER(%s)
        LIMIT %s
    """
    search_pattern = f"%{search_term}%"
    return execute_query(query, (search_pattern, search_pattern, limit))

def get_players_batch(player_ids: List[int]) -> List[Dict[str, Any]]:
    """Get multiple players by IDs"""
    if not player_ids:
        return []
    
    placeholders = ','.join(['%s'] * len(player_ids))
    query = f"""
        SELECT 
            id as playerid,
            name,
            rating as cswrating,
            country,
            photo as photourl
        FROM players
        WHERE id IN ({placeholders})
    """
    return execute_query(query, player_ids)

def get_all_players_idsonly(limit: int = None, offset: int = None) -> List[Dict[str, Any]]:
    """Get all players (ID and name only), optionally with pagination"""
    if limit is not None:
        if offset is not None:
            query = """
                SELECT id as playerid, name
                FROM players
                ORDER BY id
                LIMIT %s OFFSET %s
            """
            return execute_query(query, (limit, offset))
        else:
            query = """
                SELECT id as playerid, name
                FROM players
                ORDER BY id
                LIMIT %s
            """
            return execute_query(query, (limit,))
    else:
        query = """
            SELECT id as playerid, name
            FROM players
            ORDER BY id
        """
        return execute_query(query)
