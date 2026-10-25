from flask import Blueprint, current_app, request, jsonify
import logging
from pymysql.err import InterfaceError, OperationalError

from services.rankings_queries import get_rankings_page, get_tournament_count
from services.cache import get_cache

logger = logging.getLogger(__name__)
bp = Blueprint('rankings_v2', __name__)


def _cache():
    return get_cache()


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

        cache = _cache()
        cache_key = f"v2:rankings:{page}:{per_page}:{search or ''}"
        cache_timeout = current_app.config.get('CACHE_RANKINGS_TIMEOUT', 300)
        if cache is not None:
            cached = cache.get(cache_key)
            if cached is not None:
                return jsonify(cached)

        result = get_rankings_page(
            page=page,
            per_page=per_page,
            search=search,
        )

        if cache is not None:
            cache.set(cache_key, result, timeout=cache_timeout)
        return jsonify(result)

    except (OperationalError, InterfaceError):
        raise
    except Exception as e:
        logger.error(f"Error fetching rankings: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/v2/rankings/tournament-count')
def tournament_count():
    """Return the total number of tournaments (used as a cache-busting indicator)."""
    try:
        result = get_tournament_count()
        if not result:
            return jsonify({'error': 'No tournaments found'}), 404
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error fetching tournament count: {e}")
        return jsonify({'error': 'Internal server error'}), 500
