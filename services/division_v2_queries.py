import logging
from typing import Dict, Any, List, Optional
from services.db import execute_query, execute_query_one

logger = logging.getLogger(__name__)


def get_division_id(tourney_id: int, division_index: int) -> Optional[int]:
    """Resolve a tournament ID and division number to a divisions.id."""
    row = execute_query_one(
        """
        SELECT d.id FROM divisions d
        JOIN tournaments t ON d.tournament_id = t.id
        WHERE t.id = %s AND d.number = %s
        """,
        (tourney_id, division_index),
    )
    return row['id'] if row else None


def get_all_games_with_players(division_id: int) -> List[Dict[str, Any]]:
    """Get every game in a division with both player results and player info."""
    query = """
        SELECT
            g.id as game_id,
            g.round,
            pr1.player_id as p1_id,
            p1.name as p1_name,
            p1.rating as p1_rating,
            pr1.score as p1_score,
            pr1.result as p1_result,
            pr2.player_id as p2_id,
            p2.name as p2_name,
            p2.rating as p2_rating,
            pr2.score as p2_score,
            pr2.result as p2_result
        FROM games g
        JOIN player_results pr1
            ON pr1.game_id = g.id
        JOIN player_results pr2
            ON pr2.game_id = g.id AND pr2.player_id != pr1.player_id
        JOIN players p1 ON pr1.player_id = p1.id
        JOIN players p2 ON pr2.player_id = p2.id
        WHERE g.division_id = %s
          AND pr1.score IS NOT NULL AND pr1.score > 0
          AND pr2.score IS NOT NULL AND pr2.score > 0
        ORDER BY g.round ASC, g.id ASC
    """
    return execute_query(query, (division_id,))


def compute_division_stats(division_id: int, top_n: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """Compute all stats categories for a division.

    Stats computed:
      - highWin: highest winning scores
      - highLoss: highest losing scores
      - highSpread: biggest spreads (score - opponent_score) in wins
      - highCombined: highest combined scores
      - upsets: biggest rating differences where lower-rated player won
    """
    games = get_all_games_with_players(division_id)
    if not games:
        return {
            'highWin': [],
            'highLoss': [],
            'highSpread': [],
            'highCombined': [],
            'upsets': [],
        }

    high_win = []
    high_loss = []
    high_spread = []
    high_combined = []
    upsets = []

    for g in games:
        rnd = g['round']
        p1_id, p1_name, p1_score, p1_rating, p1_result = (
            g['p1_id'], g['p1_name'], g['p1_score'], g['p1_rating'], g['p1_result'])
        p2_id, p2_name, p2_score, p2_rating, p2_result = (
            g['p2_id'], g['p2_name'], g['p2_score'], g['p2_rating'], g['p2_result'])

        # highWin / highLoss
        if p1_result == 1:
            high_win.append({
                'player_id': p1_id, 'player_name': p1_name,
                'score': p1_score, 'opponent_id': p2_id,
                'opponent_name': p2_name, 'round': rnd,
            })
        elif p1_result == -1:
            high_loss.append({
                'player_id': p1_id, 'player_name': p1_name,
                'score': p1_score, 'opponent_id': p2_id,
                'opponent_name': p2_name, 'round': rnd,
            })

        if p2_result == 1:
            high_win.append({
                'player_id': p2_id, 'player_name': p2_name,
                'score': p2_score, 'opponent_id': p1_id,
                'opponent_name': p1_name, 'round': rnd,
            })
        elif p2_result == -1:
            high_loss.append({
                'player_id': p2_id, 'player_name': p2_name,
                'score': p2_score, 'opponent_id': p1_id,
                'opponent_name': p1_name, 'round': rnd,
            })

        # highSpread (spread on winning side only)
        if p1_result == 1:
            spread = p1_score - p2_score
            high_spread.append({
                'player_id': p1_id, 'player_name': p1_name,
                'score': p1_score, 'opponent_id': p2_id,
                'opponent_name': p2_name, 'opponent_score': p2_score,
                'spread': spread, 'round': rnd,
            })
        elif p2_result == 1:
            spread = p2_score - p1_score
            high_spread.append({
                'player_id': p2_id, 'player_name': p2_name,
                'score': p2_score, 'opponent_id': p1_id,
                'opponent_name': p1_name, 'opponent_score': p1_score,
                'spread': spread, 'round': rnd,
            })

        # highCombined
        combined = p1_score + p2_score
        high_combined.append({
            'player1_id': p1_id, 'player1_name': p1_name,
            'player2_id': p2_id, 'player2_name': p2_name,
            'total_score': combined, 'round': rnd,
        })

        # Upsets: lower-rated player beats higher-rated player
        if p1_rating is not None and p2_rating is not None:
            if p1_result == 1 and p1_rating < p2_rating:
                diff = p2_rating - p1_rating
                upsets.append({
                    'player_id': p1_id, 'player_name': p1_name,
                    'player_rating': p1_rating,
                    'opponent_id': p2_id, 'opponent_name': p2_name,
                    'opponent_rating': p2_rating,
                    'difference': diff, 'round': rnd,
                })
            elif p2_result == 1 and p2_rating < p1_rating:
                diff = p1_rating - p2_rating
                upsets.append({
                    'player_id': p2_id, 'player_name': p2_name,
                    'player_rating': p2_rating,
                    'opponent_id': p1_id, 'opponent_name': p1_name,
                    'opponent_rating': p1_rating,
                    'difference': diff, 'round': rnd,
                })

    # Sort each category and take top_n, then assign ranks
    def sort_and_rank(items, sort_key, reverse=True):
        items_sorted = sorted(items, key=sort_key, reverse=reverse)[:top_n]
        for i, item in enumerate(items_sorted):
            item['rank'] = i + 1
        return items_sorted

    return {
        'highWin': sort_and_rank(high_win, lambda x: x['score']),
        'highLoss': sort_and_rank(high_loss, lambda x: x['score']),
        'highSpread': sort_and_rank(high_spread, lambda x: x['spread']),
        'highCombined': sort_and_rank(high_combined, lambda x: x['total_score']),
        'upsets': sort_and_rank(upsets, lambda x: x['difference']),
    }


def get_division_ratings(division_id: int) -> List[Dict[str, Any]]:
    """Get rating/rank info for every player in a division, ordered by position.

    actualWins = wins + (byes as draws counted as 0.5)
    ratingChange = endRating - startRating
    """
    query = """
        SELECT
            p.id as playerid,
            p.name,
            p.country,
            tr.expected_wins as expected_wins,
            (COALESCE(tr.wins, 0) + (COALESCE(tr.byes, 0) * 0.5)) as actual_wins,
            tr.old_world_rank as old_world_rank,
            tr.new_world_rank as new_world_rank,
            tr.old_national_rank as old_nation_rank,
            tr.new_national_rank as new_nation_rank,
            tr.start_rating,
            tr.end_rating,
            (COALESCE(tr.end_rating, 0) - COALESCE(tr.start_rating, 0)) as rating_change,
            tr.old_rating_dev as start_deviation,
            tr.new_rating_dev as end_deviation
        FROM tournament_results tr
        JOIN players p ON tr.player_id = p.id
        WHERE tr.division_id = %s
        ORDER BY tr.position ASC
    """
    return execute_query(query, (division_id,))
