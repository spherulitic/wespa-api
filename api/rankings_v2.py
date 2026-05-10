from flask import Blueprint, request, jsonify
import logging

from services.rankings_queries import get_rankings_page, get_latest_tournament

logger = logging.getLogger(__name__)
bp = Blueprint('rankings_v2', __name__)


@bp.route('/v2/rankings')
def rankings():
    """Return a paginated rankings page, sorted by rating descending.

    Query parameters:
        page     - Page number (1-based, default 1)
        per_page - Players per page (default 50, max 100)
        search   - Optional player name to jump to their page
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '').strip() or None

        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 50
        if per_page > 100:
            per_page = 100

        result = get_rankings_page(
            page=page,
            per_page=per_page,
            search=search,
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error fetching rankings: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/v2/rankings/latest-tournament')
def latest_tournament():
    """Return the name and date of the most recent tournament."""
    try:
        result = get_latest_tournament()
        if not result:
            return jsonify({'error': 'No tournaments found'}), 404
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error fetching latest tournament: {e}")
        return jsonify({'error': 'Internal server error'}), 500
