from flask import Blueprint, request, jsonify
import logging

from services.tournament_search_queries import search_tournaments

logger = logging.getLogger(__name__)
bp = Blueprint('tournament_search', __name__)


@bp.route('/tournaments/search')
def tournament_search():
    """Search tournaments by name, country, and/or date range.

    All query parameters are optional, but at least one should be
    provided to avoid returning the entire dataset.

    Query parameters:
        q       - Partial tournament name (case-insensitive)
        country - 3-letter country code (e.g. GBR, USA)
        from    - Start date (YYYY-MM-DD)
        to      - End date (YYYY-MM-DD)
    """
    q = request.args.get('q', '').strip()
    country = request.args.get('country', '').strip().upper()
    from_date = request.args.get('from', '').strip()
    to_date = request.args.get('to', '').strip()

    # At least one filter is required
    if not q and not country and not from_date and not to_date:
        return jsonify({
            'tournaments': [],
            'error': 'At least one search parameter (q, country, from, to) is required'
        }), 400

    try:
        results = search_tournaments(
            q=q or None,
            country=country or None,
            from_date=from_date or None,
            to_date=to_date or None,
        )

        tournaments = []
        for r in results:
            tournament = {
                'tourneyid': r['tourneyid'],
                'name': r['name'],
                'start_date': r['start_date'].strftime('%Y-%m-%d') if r.get('start_date') else None,
                'end_date': r['end_date'].strftime('%Y-%m-%d') if r.get('end_date') else None,
                'country': r['country'],
                'location': r['location'],
            }
            tournaments.append(tournament)

        return jsonify({'tournaments': tournaments})

    except Exception as e:
        logger.error(f"Error searching tournaments: {e}")
        return jsonify({'error': 'Internal server error'}), 500
