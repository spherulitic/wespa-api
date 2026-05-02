from flask import Blueprint, request, jsonify
import logging

from services.player_v2_queries import (
    get_basic_player_v2,
    get_player_stats_v2,
    get_tournament_list_v2,
    get_tournament_rounds_v2,
)
from models.schemas import (
    PlayerResponseV2,
    PlayerStatsV2,
    TournamentListItemV2,
    TournamentResultDetailV2,
    TournamentRoundResult,
)

logger = logging.getLogger(__name__)
bp = Blueprint('player_v2', __name__)


@bp.route('/v2/player/<int:player_id>')
def get_player_v2(player_id: int):
    """Get player info with detailed stats and tournament list (v2)."""
    try:
        basic = get_basic_player_v2(player_id)
        if not basic:
            return jsonify({'error': 'Player not found'}), 404

        stats_data = get_player_stats_v2(player_id)
        stats = PlayerStatsV2(stats_data) if stats_data else PlayerStatsV2({})

        tournament_rows = get_tournament_list_v2(player_id)

        response = PlayerResponseV2({
            'playerid': basic['playerid'],
            'name': basic['name'],
            'country': basic['country'],
            'cswrating': basic['cswrating'],
            'photourl': basic['photourl'],
        })
        response.stats = stats
        response.tournaments = [TournamentListItemV2(r) for r in tournament_rows]

        return jsonify(response.to_dict())

    except Exception as e:
        logger.error(f"Error fetching v2 player {player_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/v2/player/<int:player_id>/tournaments/<int:tourney_id>')
def get_player_tournament_detail(player_id: int, tourney_id: int):
    """Get per-round details for a player at a specific tournament."""
    try:
        # Validate player exists
        basic = get_basic_player_v2(player_id)
        if not basic:
            return jsonify({'error': 'Player not found'}), 404

        rows = get_tournament_rounds_v2(player_id, tourney_id)
        if not rows:
            return jsonify({'error': 'Tournament result not found'}), 404

        # Build the tournament detail response
        # Use the first row for tournament-level info (name, date, division)
        detail = TournamentResultDetailV2({
            'playerid': player_id,
            'tourneyid': tourney_id,
            'name': rows[0].get('tournament_name', ''),
            'date': rows[0].get('tournament_date'),
            'division': rows[0].get('division_name'),
        })
        detail.rounds = [TournamentRoundResult(r) for r in rows]

        return jsonify(detail.to_dict())

    except Exception as e:
        logger.error(
            f"Error fetching tournament detail for player {player_id}, "
            f"tourney {tourney_id}: {e}"
        )
        return jsonify({'error': 'Internal server error'}), 500
