from flask import Blueprint, jsonify
import logging
import re

from services.tournament_v2_queries import (
    get_tournament_v2,
    get_divisions_for_tournament,
    get_standings_for_division,
)
from services.division_v2_queries import get_division_id, get_division_ratings
from models.schemas import (
    TournamentResponseV2,
    DivisionV2,
    DivisionStandingV2,
    DivisionRatingsResponse,
    DivisionRatingEntry,
)

logger = logging.getLogger(__name__)
bp = Blueprint('tournament_v2', __name__)


@bp.route('/v2/tournament/<int:tourney_id>')
def get_tournament(tourney_id: int):
    """Get tournament details including all divisions and standings."""
    try:
        info = get_tournament_v2(tourney_id)
        if not info:
            return jsonify({'error': 'Tournament not found'}), 404

        # Clean up the location string — remove trailing ", " if location was empty
        location = info.get('location', '')
        location = re.sub(r'^,\s*', '', location)
        location = re.sub(r',\s*$', '', location)

        response = TournamentResponseV2({
            'tourneyid': info['tourneyid'],
            'name': info['name'],
            'date': info['date'],
            'location': location or None,
        })

        divisions = get_divisions_for_tournament(tourney_id)
        for div_row in divisions:
            div = DivisionV2({
                'division': div_row['division_number'],
                'name': div_row['name'],
            })
            standings = get_standings_for_division(div_row['division_id'])
            div.standings = [DivisionStandingV2(s) for s in standings]
            response.divisions.append(div)

        return jsonify(response.to_dict())

    except Exception as e:
        logger.error(f"Error fetching tournament {tourney_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/v2/tournament/<int:tourney_id>/division/<int:division_index>/ratings')
def get_division_ratings_route(tourney_id: int, division_index: int):
    """Get rating/rank info for all players in a division."""
    try:
        tournament = get_tournament_v2(tourney_id)
        if not tournament:
            return jsonify({'error': 'Tournament not found'}), 404

        division_id = get_division_id(tourney_id, division_index)
        if not division_id:
            return jsonify({'error': 'Division not found'}), 404

        rows = get_division_ratings(division_id)
        response = DivisionRatingsResponse()
        response.ratings = [DivisionRatingEntry(r) for r in rows]

        return jsonify(response.to_dict())

    except Exception as e:
        logger.error(
            f"Error fetching division ratings for tournament {tourney_id}, "
            f"division {division_index}: {e}"
        )
        return jsonify({'error': 'Internal server error'}), 500
