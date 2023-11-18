
class Match:
    def __init__(self, match_id, winner, date):
        self.match_id = match_id
        self.allies_players = []
        self.axis_players = []
        self.winner = winner
        self.date = date

    def add_player(self, match_player):
        if match_player.side == "ALLIES":
            self.allies_players.append(match_player)
        else:
            self.axis_players.append(match_player)
