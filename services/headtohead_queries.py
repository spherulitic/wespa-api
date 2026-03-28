import logging
from typing import List
from services.db import execute_query
from models.schemas import HeadToHeadGame

logger = logging.getLogger(__name__)

def get_head_to_head_games(player_ids: List[int]) -> List[HeadToHeadGame]:
    """Get all head-to-head games between specified players"""
    if len(player_ids) < 2:
        return []
    
    placeholders = ','.join(['%s'] * len(player_ids))
    
    # Query to find games between any two players in the list
    query = f"""
        SELECT DISTINCT
            g.id as gameid,
            t.start_date as date,
            t.name as tourneyname,
            pr1.player_id as player1_id,
            p1.name as player1_name,
            pr1.score as player1_score,
            tr1.start_rating as player1_oldrating,
            tr1.start_rating as player1_newrating,
            tr1.position as player1_position,
            pr2.player_id as player2_id,
            p2.name as player2_name,
            pr2.score as player2_score,
            tr2.start_rating as player2_oldrating,
            tr2.start_rating as player2_newrating,
            tr2.position as player2_position,
            g.gcg_filename as annotated
        FROM games g
        JOIN player_results pr1 ON g.id = pr1.game_id
        JOIN player_results pr2 ON g.id = pr2.game_id AND pr1.player_id != pr2.player_id
        JOIN players p1 ON pr1.player_id = p1.id
        JOIN players p2 ON pr2.player_id = p2.id
        JOIN divisions d ON g.division_id = d.id
        JOIN tournaments t ON d.tournament_id = t.id
        LEFT JOIN tournament_results tr1 ON tr1.player_id = pr1.player_id 
            AND tr1.division_id = d.id
        LEFT JOIN tournament_results tr2 ON tr2.player_id = pr2.player_id 
            AND tr2.division_id = d.id
        WHERE pr1.player_id IN ({placeholders})
          AND pr2.player_id IN ({placeholders})
        ORDER BY t.start_date DESC
    """
    
    # Need to pass player_ids twice (once for each side of the join)
    params = player_ids + player_ids
    results = execute_query(query, params)
    
    return [HeadToHeadGame(r) for r in results]
