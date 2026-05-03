from flask import Blueprint, jsonify
import logging

from services.tournament_v2_queries import get_tournament_v2
from services.division_v2_queries import get_division_id, compute_division_stats
from models.schemas import DivisionStatsResponse, DivisionStatEntry

logger = logging.getLogger(__name__)
bp = Blueprint('division_stats_v2', __name__)


@bp.route('/v2/tournament/<int:tourney_id>/division/<int:division_index>/stats')
def get_division_stats(tourney_id: int, division_index: int):
    """Get detailed stats for a specific division in a tournament."""
    try:
        # Validate the tournament exists
        tournament = get_tournament_v2(tourney_id)
        if not tournament:
            return jsonify({'error': 'Tournament not found'}), 404

        # Resolve division number to internal division_id
        division_id = get_division_id(tourney_id, division_index)
        if not division_id:
            return jsonify({'error': 'Division not found'}), 404

        # Compute all stats
        stats_data = compute_division_stats(division_id)

        response = DivisionStatsResponse()
        for category in ('highWin', 'highLoss', 'highSpread', 'highCombined', 'upsets'):
            entries = stats_data.get(category, [])
            setattr(response, category, [DivisionStatEntry(e) for e in entries])

        return jsonify(response.to_dict())

    except Exception as e:
        logger.error(
            f"Error fetching division stats for tournament {tourney_id}, "
            f"division {division_index}: {e}"
        )
        return jsonify({'error': 'Internal server error'}), 500
