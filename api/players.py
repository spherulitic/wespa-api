from flask import Blueprint, request, jsonify
import logging
from typing import List

from services.player_queries import (
    search_players,
    get_players_batch,
    get_all_players_idsonly,
    get_basic_player,
    get_player_career_totals,
    get_player_ranking
)
from models.schemas import CrossTablesPlayer

logger = logging.getLogger(__name__)
bp = Blueprint('players', __name__)

def build_basic_player_response(player_data):
    """Build basic player response from raw data"""
    totals = get_player_career_totals(player_data['playerid'])
    ranking = get_player_ranking(player_data['playerid'])
    
    player_dict = {
        'playerid': int(player_data['playerid']),
        'name': player_data['name'],
        'cswrating': int(player_data['cswrating']) if player_data['cswrating'] else None,
        'cswranking': int(ranking) if ranking else None,
        'w': int(totals['wins']),
        'l': int(totals['losses']),
        't': int(totals['ties']),
        'b': int(totals['byes']),
        'photourl': player_data.get('photourl'),
        'country': player_data.get('country'),
        'twlrating': None,
        'twlranking': None,
        'city': None,
        'state': None
    }
    
    return player_dict

@bp.route('/players.php')
def get_players():
    """Handle multiple players endpoint with various parameters"""
    p = request.args.get('p')
    search = request.args.get('search')
    idsonly = request.args.get('idsonly') == '1'
    
    # Case 1: Get players by ID list (batch)
    if p:
        # Parse space-separated IDs (XT format: ?p=6003+17589), limit to 50
        try:
            ids = [int(x.strip()) for x in p.replace('+', ' ').split() if x.strip()]
            if len(ids) > 50:
                ids = ids[:50]
            
            if idsonly:
                # This case shouldn't typically happen with playerlist
                players = [{'playerid': pid, 'name': f'Player {pid}'} for pid in ids]
            else:
                players_data = get_players_batch(ids)
                players = [build_basic_player_response(p) for p in players_data]
            
            return jsonify({'players': players})
        
        except ValueError:
            return jsonify({'players': []}), 200
    
    # Case 2: Search by name
    elif search:
        if idsonly:
            # Return only IDs and names
            results = search_players(search)
            idsonly_results = [{'playerid': r['playerid'], 'name': r['name']} for r in results]
            return jsonify({'players': idsonly_results})
        else:
            # Return full player data
            results = search_players(search)
            players = []
            for r in results:
                player_data = build_basic_player_response(r)
                players.append(player_data)
            return jsonify({'players': players})
    
    # Case 3: Get all players (ID only)
    elif idsonly:
        offset = request.args.get('offset', type=int)
        limit = request.args.get('limit', type=int)
        players = get_all_players_idsonly(limit=limit, offset=offset)
        return jsonify({'players': players})
    
    # No valid parameters
    return jsonify([]), 200
