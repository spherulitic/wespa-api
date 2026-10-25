import os
from flask import Blueprint, current_app, request, jsonify
import logging
from pymysql.err import InterfaceError, OperationalError

from services.player_v2_queries import (
    get_basic_player_v2,
    get_player_stats_v2,
    get_tournament_list_v2,
    get_tournament_rounds_v2,
    compute_peak_ratings,
)
from services.player_queries import update_player_country
from services.cache import get_cache
from models.schemas import (
    PlayerResponseV2,
    PlayerStatsV2,
    TournamentListItemV2,
    TournamentResultDetailV2,
    TournamentRoundResult,
)

logger = logging.getLogger(__name__)
bp = Blueprint('player_v2', __name__)


def _cache():
    return get_cache()


def _player_cache_key(player_id: int) -> str:
    return f"v2:player:{player_id}"


def _invalidate_player_cache(player_id: int) -> None:
    cache = _cache()
    if cache is not None:
        cache.delete(_player_cache_key(player_id))


@bp.route('/v2/player/<int:player_id>')
def get_player_v2(player_id: int):
    """Get player info with detailed stats and tournament list (v2)."""
    try:
        cache_key = _player_cache_key(player_id)
        cache_timeout = current_app.config.get('CACHE_PLAYER_TIMEOUT', 300)
        cache = _cache()
        if cache is not None:
            cached = cache.get(cache_key)
            if cached is not None:
                return jsonify(cached)

        basic = get_basic_player_v2(player_id)
        if not basic:
            return jsonify({'error': 'Player not found'}), 404

        stats_data = get_player_stats_v2(player_id)
        stats = PlayerStatsV2(stats_data) if stats_data else PlayerStatsV2({})

        tournament_rows = get_tournament_list_v2(player_id)
        peak_2yr, peak_all = compute_peak_ratings(tournament_rows)

        response = PlayerResponseV2({
            'playerid': basic['playerid'],
            'name': basic['name'],
            'country': basic['country'],
            'cswrating': basic['cswrating'],
            'photourl': basic['photourl'],
            'title': basic.get('title'),
            'norms': basic.get('norms'),
            'peakRatingLastTwoYears': peak_2yr,
            'peakRatingAllTime': peak_all,
        })
        response.stats = stats
        response.tournaments = [TournamentListItemV2(r) for r in tournament_rows]

        payload = response.to_dict()
        if cache is not None:
            cache.set(cache_key, payload, timeout=cache_timeout)
        return jsonify(payload)

    except (OperationalError, InterfaceError):
        raise
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

    except (OperationalError, InterfaceError):
        raise
    except Exception as e:
        logger.error(
            f"Error fetching tournament detail for player {player_id}, "
            f"tourney {tourney_id}: {e}"
        )
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/v2/player/country', methods=['PUT'])
def update_player_country_endpoint():
    """
    Update player nationality.
    Accepts JSON body with list of {player_id: int, trigraph: str} pairs.
    Requires Authorization header with valid API key (from UPDATE_API_KEY env).
    """
    # Authenticate
    api_key = os.environ.get('UPDATE_API_KEY')
    if not api_key:
        return jsonify({'error': 'Server misconfiguration: UPDATE_API_KEY not set'}), 500

    auth = request.headers.get('Authorization', '')
    # Accept raw key or Bearer scheme
    if auth.startswith('Bearer '):
        provided_key = auth[len('Bearer '):]
    else:
        provided_key = auth
    if provided_key != api_key:
        return jsonify({'error': 'Unauthorized: invalid API key'}), 401

    # Parse body
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({'error': 'Invalid JSON'}), 400

    if not isinstance(data, list):
        return jsonify({'error': 'Request body must be a JSON array of objects'}), 400

    if not data:
        return jsonify({'error': 'Empty update list'}), 400

    results = []
    for idx, entry in enumerate(data):
        if not isinstance(entry, dict):
            results.append({
                'index': idx,
                'player_id': None,
                'trigraph': None,
                'status': 'invalid_entry'
            })
            continue

        player_id = entry.get('player_id')
        trigraph = entry.get('trigraph')

        # Validate player_id
        if not isinstance(player_id, int) or player_id <= 0:
            results.append({
                'index': idx,
                'player_id': player_id,
                'trigraph': trigraph,
                'status': 'invalid_player_id'
            })
            continue

        # Validate trigraph (exactly 3 characters, will uppercase)
        if not isinstance(trigraph, str) or len(trigraph) != 3:
            results.append({
                'index': idx,
                'player_id': player_id,
                'trigraph': trigraph,
                'status': 'invalid_trigraph'
            })
            continue

        trigraph_clean = trigraph.strip().upper()

        try:
            success = update_player_country(player_id, trigraph_clean)
            if success:
                _invalidate_player_cache(player_id)
                results.append({
                    'index': idx,
                    'player_id': player_id,
                    'trigraph': trigraph_clean,
                    'status': 'updated'
                })
            else:
                results.append({
                    'index': idx,
                    'player_id': player_id,
                    'trigraph': trigraph_clean,
                    'status': 'player_not_found'
                })
        except Exception as e:
            logger.error(f"Database error updating player {player_id}: {e}")
            results.append({
                'index': idx,
                'player_id': player_id,
                'trigraph': trigraph_clean,
                'status': 'database_error'
            })

    # Determine overall HTTP status
    all_ok = all(r['status'] == 'updated' for r in results)
    status_code = 200 if all_ok else 207
    return jsonify({'results': results}), status_code
