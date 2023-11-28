import csv
from datetime import datetime
from pprint import pprint

from openskill.models import PlackettLuce
from trueskill import Rating, rate

from models.player import Player
from models.match import Match
from models.match_player import MatchPlayer

players_by_name = {}

ALLIES = "Allies"
AXIS = "Axis"

doc_to_side = {
    "ALLY": ALLIES,
    "CMW": ALLIES,
    "AXIS": AXIS,
    "PE": AXIS
}

mu = 25.0
sigma = 25.0 / 3.0
model = PlackettLuce(mu=mu, sigma=sigma)


def get_side_from_doctrine(doctrine):
    const = doctrine.split(".")[1]
    return doc_to_side[const]


def parse_date(raw_date):
    return datetime.strptime(raw_date, "%d/%m/%y")


# Parse the row to get match id and a MatchPlayer object for the player
def handle_csv_row(row):
    # Find player if exists
    name = row["Player"]

    # If exists, grab Player model
    if name in players_by_name:
        player = players_by_name[name]
    else:
        # Create a new Player model for this name
        os_rating = model.rating(name=name)
        ts_rating = Rating(mu=mu, sigma=sigma)
        player = Player(name, os_rating, ts_rating)
        players_by_name[name] = player

    side = get_side_from_doctrine(row["Doctrine"])
    match_player = MatchPlayer(name, side, player.os_rating, player.ts_rating, player.last_played)

    return row["Game-ID"], parse_date(row["Date"]), row["Winner"], match_player


def update_sigma_decay(os_rating, ts_rating, weeks_since_last_played):
    # Within 3 weeks, no decay
    if weeks_since_last_played > 3:
        weeks_since_last_played -= 3

        # 0.05 decay per week
        decay = 0.05 * weeks_since_last_played
        os_rating.sigma = min(sigma, os_rating.sigma + decay)
        ts_rating = Rating(mu=ts_rating.mu, sigma=min(sigma, ts_rating.sigma + decay))

    return os_rating, ts_rating

# Run rating update for the players in the match
def process_match(match):
    match_date = match.date
    # For each player, get last played date
    # Calculate sigma decay if necessary and update rating
    for match_player in match.allies_players + match.axis_players:
        weeks_since_last_played = match_player.weeks_since_last_played(match_date)
        os_rating, ts_rating = update_sigma_decay(match_player.os_rating, match_player.ts_rating,
                                                  weeks_since_last_played)
        match_player.os_rating = os_rating
        match_player.ts_rating = ts_rating

    # Build lists of team ratings
    # Rate the match using the model (first team is the winner)
    allies_os_ratings = [mp.os_rating for mp in match.allies_players]
    axis_os_ratings = [mp.os_rating for mp in match.axis_players]

    allies_ts_ratings = {mp.name: mp.ts_rating for mp in match.allies_players}
    axis_ts_ratings = {mp.name: mp.ts_rating for mp in match.axis_players}

    if match.winner == ALLIES:
        os_teams = [allies_os_ratings, axis_os_ratings]
        allies_os_ratings, axis_os_ratings = model.rate(os_teams)
        ts_teams = [allies_ts_ratings, axis_ts_ratings]
        allies_ts_ratings, axis_ts_ratings = rate(ts_teams)
    else:
        os_teams = [axis_os_ratings, allies_os_ratings]
        axis_os_ratings, allies_os_ratings = model.rate(os_teams)
        ts_teams = [axis_ts_ratings, allies_ts_ratings]
        axis_ts_ratings, allies_ts_ratings = rate(ts_teams)

    # Update player ratings and last played date
    for os_rating in allies_os_ratings + axis_os_ratings:
        name = os_rating.name
        player = players_by_name[name]
        player.update_os_rating(os_rating, match_date)

    for name, ts_rating in allies_ts_ratings.items():
        player = players_by_name[name]
        player.update_ts_rating(ts_rating)
        player.update_win_loss(match.winner == ALLIES)
    for name, ts_rating in axis_ts_ratings.items():
        player = players_by_name[name]
        player.update_ts_rating(ts_rating)
        player.update_win_loss(match.winner != ALLIES)

def get_min_max_mu(players):
    os_min = 100
    os_max = 0
    ts_min = 100
    ts_max = 0
    for player in players:
        os_mu = player.os_rating.mu
        ts_mu = player.ts_rating.mu

        os_min = min(os_mu, os_min)
        os_max = max(os_mu, os_max)

        ts_min = min(ts_mu, ts_min)
        ts_max = max(ts_mu, ts_max)

    return os_min, os_max, ts_min, ts_max

def normalise_to_elo(mu, old_min, old_max):
    new_min = 1000
    new_max = 2000
    return ((mu - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min


def parse_csv(filename):
    with open(f"{filename}", newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')

        matches = 0
        current_match = None
        for row in reader:
            match_id, match_date, match_winner, match_player = handle_csv_row(row)

            # For first match in the dataset, current_match_id is None, skip
            # Otherwise, if current_match_id is different from match_id, we know we've reached a new match,
            # and we should process the current match players
            if current_match is not None and match_id != current_match.match_id:
                process_match(current_match)
                matches += 1

            # Reset the current match id and players
            if current_match is None or match_id != current_match.match_id:
                current_match = Match(match_id, match_winner, match_date)

            current_match.add_player(match_player)

        # At end of iteration, process the final match
        if len(current_match.allies_players) == len(current_match.axis_players):
            process_match(current_match)

    pprint(players_by_name)

    os_min, os_max, ts_min, ts_max = get_min_max_mu(list(players_by_name.values()))

    with open('output-decay.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(
            ["name", "games played", "wins", "losses", "last_played", "os_elo", "os_mu", "os_sigma", "os_rank",
             "ts_elo", "ts_mu", "ts_sigma"])
        keys = list(players_by_name.keys())
        keys.sort()
        for key in keys:
            player = players_by_name[key]
            os_elo = normalise_to_elo(player.os_rating.mu, os_min, os_max)
            ts_elo = normalise_to_elo(player.ts_rating.mu, ts_min, ts_max)
            writer.writerow([player.name, player.games_played, player.wins, player.losses, player.last_played,
                             os_elo, player.os_rating.mu, player.os_rating.sigma, player.os_rating.ordinal(),
                             ts_elo, player.ts_rating.mu, player.ts_rating.sigma])


if __name__ == '__main__':
    parse_csv("dataset.csv")
