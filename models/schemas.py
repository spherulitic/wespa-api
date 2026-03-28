from typing import Optional, List, Dict, Any

class TournamentResult:
    def __init__(self, data: Dict[str, Any]):
        self.tourneyid = data.get('tourneyid')
        self.name = data.get('name')
        self.date = data.get('date')
        self.division = data.get('division')
        self.wins = data.get('wins')
        self.losses = data.get('losses')
        self.ties = data.get('ties', 0)
        self.place = data.get('place')
        self.totalplayers = data.get('totalplayers')
        self.rating = data.get('rating')
        self.ratingchange = data.get('ratingchange')
        self.points = data.get('points')
        self.averagepoints = data.get('averagepoints')
    
    def to_dict(self):
        return {
            'tourneyid': self.tourneyid,
            'name': self.name,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'division': self.division,
            'wins': self.wins,
            'losses': self.losses,
            'ties': self.ties,
            'place': self.place,
            'totalplayers': self.totalplayers,
            'rating': self.rating,
            'ratingchange': self.ratingchange,
            'points': self.points,
            'averagepoints': self.averagepoints
        }

class CrossTablesPlayer:
    def __init__(self, data: Dict[str, Any]):
        self.playerid = data.get('playerid')
        self.name = data.get('name')
        self.cswrating = data.get('cswrating')
        self.cswranking = data.get('cswranking')
        self.twlrating = None  # Always null per spec
        self.twlranking = None  # Always null per spec
        self.w = data.get('wins', 0)
        self.l = data.get('losses', 0)
        self.t = data.get('ties', 0)
        self.b = data.get('byes', 0)
        self.photourl = data.get('photourl')
        self.city = None  # Not available
        self.state = None  # Not available
        self.country = data.get('country')
        self.tournamentCount = data.get('tournament_count')
        self.averageScore = data.get('average_score')
        self.opponentAverageScore = data.get('opponent_average_score')
        self.results = []
    
    def to_dict(self, include_results=False):
        result = {
            'playerid': self.playerid,
            'name': self.name,
            'twlrating': self.twlrating,
            'cswrating': self.cswrating,
            'twlranking': self.twlranking,
            'cswranking': self.cswranking,
            'w': int(self.w) if self.w is not None else 0,
            'l': int(self.l) if self.l is not None else 0,
            't': int(self.t) if self.t is not None else 0,
            'b': int(self.b) if self.b is not None else 0,
            'photourl': self.photourl,
            'city': self.city,
            'state': self.state,
            'country': self.country
        }
        
        if include_results:
            result.update({
                'tournamentCount': self.tournamentCount,
                'averageScore': float(self.averageScore) if self.averageScore else None,
                'opponentAverageScore': float(self.opponentAverageScore) if self.opponentAverageScore else None,
                'results': [r.to_dict() for r in self.results]
            })
        
        return result

class HeadToHeadGame:
    def __init__(self, data: Dict[str, Any]):
        self.gameid = data.get('gameid')
        self.date = data.get('date')
        self.tourneyname = data.get('tourneyname')
        self.player1 = {
            'playerid': data.get('player1_id'),
            'name': data.get('player1_name'),
            'score': data.get('player1_score'),
            'oldrating': data.get('player1_oldrating'),
            'newrating': data.get('player1_newrating'),
            'position': data.get('player1_position')
        }
        self.player2 = {
            'playerid': data.get('player2_id'),
            'name': data.get('player2_name'),
            'score': data.get('player2_score'),
            'oldrating': data.get('player2_oldrating'),
            'newrating': data.get('player2_newrating'),
            'position': data.get('player2_position')
        }
        self.annotated = data.get('annotated')
    
    def to_dict(self):
        return {
            'gameid': self.gameid,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'tourneyname': self.tourneyname,
            'player1': self.player1,
            'player2': self.player2,
            'annotated': self.annotated
        }
