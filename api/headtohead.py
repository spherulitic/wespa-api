from flask import Blueprint, request, jsonify
import logging
import re

from services.headtohead_queries import get_head_to_head_games

logger = logging.getLogger(__name__)
bp = Blueprint('headtohead', __name__)

def parse_player_ids(players_param: str) -> list:
    """Parse player IDs from various separator formats"""
    if not players_param:
        return []
    
    # Replace common separators with comma
    players_param = players_param.replace('+', ',').replace(' ', ',')
    
    # Split by comma and parse integers
    ids = []
    for part in players_param.split(','):
        part = part.strip()
        if part:
            try:
                ids.append(int(part))
            except ValueError:
                continue
    
    return ids

@bp.route('/headtohead.php')
def get_headtohead():
    """Get head-to-head games between players"""
    players_param = request.args.get('players')
    
    if not players_param:
        return jsonify([]), 200
    
    player_ids = parse_player_ids(players_param)
    
    if len(player_ids) < 2:
        return jsonify([]), 200
    
    try:
        games = get_head_to_head_games(player_ids)
        return jsonify([game.to_dict() for game in games])
    
    except Exception as e:
        logger.error(f"Error fetching head-to-head games for {player_ids}: {e}")
        return jsonify([]), 200
