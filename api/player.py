from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

from services.player_queries import (
    get_basic_player, 
    get_player_career_totals, 
    get_player_ranking,
    get_tournament_history
)
from models.schemas import CrossTablesPlayer

logger = logging.getLogger(__name__)
bp = Blueprint('player', __name__)

def get_player_data(player_id, include_results=False):
    """Helper to fetch and build player data"""
    # Get basic player info
    basic = get_basic_player(player_id)
    if not basic:
        return None
    
    # Get career totals
    totals = get_player_career_totals(player_id)
    
    # Get ranking
    ranking = get_player_ranking(player_id)
    
    # Build player object
    player_data = {
        'playerid': basic['playerid'],
        'name': basic['name'],
        'cswrating': basic['cswrating'],
        'cswranking': ranking,
        'wins': totals['wins'],
        'losses': totals['losses'],
        'ties': totals['ties'],
        'byes': totals['byes'],
        'photourl': basic['photourl'],
        'country': basic['country']
    }
    
    player = CrossTablesPlayer(player_data)
    
    # Add tournament history if requested
    if include_results:
        results = get_tournament_history(player_id)
        player.results = results
        
        # Calculate aggregates
        if results:
            total_points = sum(r.points for r in results if r.points)
            total_games = sum((r.wins + r.losses + r.ties) for r in results)
            player.tournamentCount = len(results)
            player.averageScore = total_points / total_games if total_games > 0 else 0
            # Note: opponentAverageScore would require additional calculations
            player.opponentAverageScore = None
    
    return player

@bp.route('/player.php')
def get_player():
    """Get player information"""
    player_id = request.args.get('player', type=int)
    include_results = request.args.get('results') == '1'
    
    if not player_id:
        return jsonify({}), 200
    
    try:
        player = get_player_data(player_id, include_results)
        if not player:
            return jsonify({}), 200
        
        return jsonify(player.to_dict(include_results))
    
    except Exception as e:
        logger.error(f"Error fetching player {player_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500
