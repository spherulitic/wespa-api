from datetime import date

from services.player_v2_queries import compute_peak_ratings


def _tournament(tourney_id, when, wins, losses, byes, end_rating):
    return {
        "tourneyid": tourney_id,
        "date": when,
        "wins": wins,
        "losses": losses,
        "draws": byes,
        "end_rating": end_rating,
    }


def test_peak_ratings_ignore_provisional_tournaments():
    today = date(2026, 1, 1)
    tournaments = [
        _tournament(1, date(2025, 1, 1), 25, 0, 0, 1700),
        _tournament(2, date(2025, 6, 1), 25, 0, 0, 1800),
        _tournament(3, date(2025, 9, 1), 10, 0, 0, 1750),
    ]

    peak_2y, peak_all = compute_peak_ratings(tournaments, today=today)
    assert peak_all == 1800
    assert peak_2y == 1800


def test_peak_ratings_split_all_time_and_two_year_windows():
    today = date(2026, 1, 1)
    tournaments = [
        _tournament(1, date(2023, 1, 1), 100, 0, 0, 1900),
        _tournament(2, date(2025, 6, 1), 60, 0, 0, 1800),
    ]

    peak_2y, peak_all = compute_peak_ratings(tournaments, today=today)
    assert peak_all == 1900
    assert peak_2y == 1800


def test_peak_ratings_are_deterministic_for_same_date_tournaments():
    today = date(2026, 1, 1)
    same_date = date(2025, 6, 1)
    tournaments = [
        _tournament(2, same_date, 50, 0, 0, 1800),
        _tournament(1, same_date, 50, 0, 0, 1750),
    ]

    peak_2y, peak_all = compute_peak_ratings(tournaments, today=today)
    assert peak_all == 1800
    assert peak_2y == 1800


def test_peak_ratings_empty_history():
    assert compute_peak_ratings([]) == (None, None)
