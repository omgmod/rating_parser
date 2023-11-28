from audioop import mul
import json
from multiprocessing.spawn import old_main_modules
import os
import datetime
import re
import matplotlib.pyplot as plt
import datetime
from matplotlib.dates import date2num
import pandas as pd
from get_player_company import get_companies
import locale
from trueskill import Rating, quality, rate, setup
import trueskill
import tqdm

locale.getpreferredencoding(False)

# only calc for games after:
process_date = datetime.datetime(2010, 1, 1)

standard_env = trueskill.TrueSkill(draw_probability=0)  # ,
teams_env = trueskill.TrueSkill(draw_probability=0)  # ,
# mu=1500,
# sigma=320,
# beta=100,
# tau=3.2)

faction_dict = {'OMGUPG.CMW.ROYALENGIESDOC': 'Allies',
                'OMGUPG.CMW.ARTYDOC': 'Allies',
                'OMGUPG.ALLY.INFANTRYDOC': 'Allies',
                'OMGUPG.ALLY.ARMOURDOC': 'Allies',
                'OMGUPG.ALLY.AIRBORNEDOC': 'Allies',
                'OMGUPG.CMW.COMMANDODOC': 'Allies',
                'OMGUPG.SOV.BREAKTHROUGHDOC': 'ALLY',
                'OMGUPG.SOV.PROPAGANDADOC': 'ALLY',
                'OMGUPG.SOV.URBANDOC': 'ALLY',

                'OMGUPG.PE.SCORCHEDDOC': 'Axis',
                'OMGUPG.PE.TANKHUNTERDOC': 'Axis',
                'OMGUPG.PE.LUFTDOC': 'Axis',
                'OMGUPG.AXIS.TERRORDOC': 'Axis',
                'OMGUPG.AXIS.BLITZDOC': 'Axis',
                'OMGUPG.AXIS.DEFENSEDOC': 'Axis',
                'OMGUPG.OST.ELITE': 'AXIS',
                'OMGUPG.OST.FORTRESS': 'AXIS',
                'OMGUPG.OST.SUPPORT': 'AXIS', }

sub_faction_dict = {'OMGUPG.CMW.ROYALENGIESDOC': 'CMW',
                    'OMGUPG.CMW.ARTYDOC': 'CMW',
                    'OMGUPG.ALLY.INFANTRYDOC': 'ALLY',
                    'OMGUPG.ALLY.ARMOURDOC': 'ALLY',
                    'OMGUPG.ALLY.AIRBORNEDOC': 'ALLY',
                    'OMGUPG.CMW.COMMANDODOC': 'CMW',
                    'OMGUPG.SOV.BREAKTHROUGHDOC': 'ALLY',
                    'OMGUPG.SOV.PROPAGANDADOC': 'ALLY',
                    'OMGUPG.SOV.URBANDOC': 'ALLY',

                    'OMGUPG.PE.SCORCHEDDOC': 'PE',
                    'OMGUPG.PE.TANKHUNTERDOC': 'PE',
                    'OMGUPG.PE.LUFTDOC': 'PE',
                    'OMGUPG.AXIS.TERRORDOC': 'AXIS',
                    'OMGUPG.AXIS.BLITZDOC': 'AXIS',
                    'OMGUPG.AXIS.DEFENSEDOC': 'AXIS',
                    'OMGUPG.OST.ELITE': 'AXIS',
                    'OMGUPG.OST.FORTRESS': 'AXIS',
                    'OMGUPG.OST.SUPPORT': 'AXIS',
                    }

# open smurf comparison dict
smurfs = pd.read_csv('smurf_dict.csv', index_col=0)


def real_name(player):
    try:
        return smurfs.loc[player][0]
    except KeyError:
        return player


print(real_name("RIFLEMASTER2000"))
print(real_name("STORMTROUT"))


class Game(object):

    def __init__(self, date, id, winner, map):
        self.date = date
        self.id = id
        self.winner = winner
        self.map = map
        self.players = []
        self.factions = {"winners": [],
                         "losers": []}


class Player(object):

    def __init__(self):
        self.games = {}
        self.wins = 0
        self.losses = 0
        self.alliedWins = 0
        self.alliedLosses = 0
        self.axisWins = 0
        self.axisLosses = 0
        self.totalElo = 1500
        self.alliedElo = 1500
        self.axisElo = 1500
        self.trueskill = standard_env.Rating()
        self.britTrueSkill = teams_env.Rating()
        self.amerTrueSkill = teams_env.Rating()
        self.peTrueSkill = teams_env.Rating()
        self.axisTrueSkill = teams_env.Rating()
        self.eloDifference = 0
        self.eloChanges = []

    def add_game(self, date, id, faction, side, gameWinner, company):
        # print(date, id, faction, gameWinner)
        pass

    def eloAdd(self, amount):
        self.totalElo += amount

    def return_faction_true(self, faction):

        if faction == "CMW":
            return self.britTrueSkill
        elif faction == "ALLY":
            return self.amerTrueSkill
        elif faction == "AXIS":
            return self.axisTrueSkill
        elif faction == "PE":
            return self.peTrueSkill

    def set_faction_true(self, faction, skill):

        if faction == "CMW":
            self.britTrueSkill = skill
        elif faction == "ALLY":
            self.amerTrueSkill = skill
        elif faction == "AXIS":
            self.axisTrueSkill = skill
        elif faction == "PE":
            self.peTrueSkill = skill


folder = 'G:/OMG BACKUP/htdocs/warcp2/tmp'
sga_unpacked_folder = 'G:/New folder (4)'
preGameReports = []
postGameReports = []
preGameCallIns = []

for r, _, fileNames in os.walk(folder):
    for fileName in fileNames:
        if 'sga' in fileName:
            preGameReports.append(r + '/' + fileName)


        elif 'newbattlereport' in fileName:
            postGameReports.append(fileName)


        elif '.ucs' in fileName:
            preGameCallIns.append(r + '/' + fileName)

games = {}
reportDupeList = []
# TODO
# DROP DETECTION LIKE IN GAME 899 FEB 2022
for report in tqdm.tqdm(postGameReports[:]):
    parse = True
    with open(os.path.join(folder, report)) as file:
        file_contents = file.readlines()
        # print(file_contents)

        for line in file_contents:
            if "%_POST['final'] => 0" in line:
                # not the final dump
                parse = False
            if "%_POST['raceWinner'] =>" in line:
                if 'Allies' in line:
                    gameWinner = 'Allies'
                elif 'Axis' in line:
                    gameWinner = 'Axis'
                else:
                    gameWinner = 'Draw'
            if "%_POST['dropPlayers']" in line:
                if len(line[line.find('=>') + 3:]) > 1:
                    drops = True
                else:
                    drops = False

            if "%_POST['timeElapsed'] => " in line:
                time = float(line[line.find('=>') + 3:]) / 60

            if "%_POST['map']" in line:
                map = line[line.find('=>') + 3:]

            if "%_POST['battleID']" in line:
                id = int(line[line.find('=>') + 3:])

        dateStamp = os.path.getmtime(folder + '/' + report)
        datetimeObject = datetime.datetime.fromtimestamp(dateStamp)
        date = datetimeObject.strftime('%d/%m/%y')
        subList = [date, id]

        if time < 15 and drops == True:
            parse = False
        if parse:
            if subList not in reportDupeList:
                if gameWinner == 'Allies' or gameWinner == 'Axis':
                    reportDupeList.append([date, id])
                    game = Game(date,
                                id,
                                gameWinner,
                                map)
                    games[(game.date, game.id)] = game


def list_cleanse(listy):
    returnList = []
    for listitem in listy:
        result = re.search(r'[0-9A-Za-z].*', listitem)
        if result:
            returnList.append(listitem)
    return returnList


players = {}
missing_games = []
for key in games:
    print(key)

all_comps = {}

for report in tqdm.tqdm(preGameReports[:]):
    with open(report, errors='ignore') as file:

        try:
            comps = get_companies(report)
        except:
            # badly formed report
            comps = False
        dateStamp = os.path.getmtime(report)
        datetimeObject = datetime.datetime.fromtimestamp(dateStamp)
        date = datetimeObject.strftime('%d/%m/%y')
        date2 = datetimeObject - datetime.timedelta(days=1)
        date2 = date2.strftime('%d/%m/%y')
        game_date = date
        file_contents = file.read()
        file_contents = re.split(r'\n', file_contents)
        file_contents = [file.strip() for file in file_contents]
        file_contents = list_cleanse(file_contents)
        # print(file_contents)
        player_list = []
        player_name = ""
        success = False
        for file_line in file_contents:

            if "BattleID" in file_line:
                # print(file_line)
                id = int(file_line[file_line.find('=') + 2:])
                # rint(id)

            if "Player[pid].Name ==" in file_line:
                player_name = real_name(file_line[file_line.find("==") + 4:-6].upper())
                if comps:
                    company = comps[player_name]
                # check existance of player
                if player_name in players:
                    # exists
                    pass
                else:
                    # new player
                    players[player_name] = Player()

            if "Player[pid].Doctrine" in file_line:
                faction = file_line[file_line.find("=") + 2:].upper()
                player_list.append([player_name, faction])
                faction_dict[faction]
                success = False
                try:
                    players[player_name].add_game(date, id, faction, faction_dict[faction], games[(date, id)].winner,
                                                  company)
                    success = True
                except KeyError:
                    i = -10

                    while True:
                        i += 1
                        date2 = datetimeObject - datetime.timedelta(days=i)

                        date2 = date2.strftime('%d/%m/%y')

                        try:
                            players[player_name].add_game(date2, id, faction, faction_dict[faction],
                                                          games[(date2, id)].winner, company)
                            date = date2
                            success = True
                            break
                        except KeyError:
                            if i > 10:
                                # print(f'date {date}  id {id}  missing from games')
                                break
            if success:
                all_comps[str((date, id))] = comps
        try:
            games[(date, id)].players = player_list
        except:
            try:
                games[(date2, id)].players = player_list
            except:
                missing_games.append([date, id])
        # print(file_contents[1])

game_list = list(games.items())
game_list = sorted(game_list, key=lambda x: (int(x[1].date[6:8] + x[1].date[3:5] + x[1].date[0:2]), x[1].id))

# Filter by date
game_list_new = []
for game in game_list:
    if datetime.datetime.strptime(game[1].date, '%d/%m/%y') > datetime.datetime.strptime('01/01/19', '%d/%m/%y'):
        game_list_new.append(game)

game_list = game_list_new


def calc_elo(winning_team_elo, losing_team_elo):
    # speed of rating change
    k = 32

    r1 = 10 ** (winning_team_elo / 400.0)
    r2 = 10 ** (losing_team_elo / 400.0)

    e1 = r1 / (r1 + r2)
    e2 = r2 / (r1 + r2)

    winning_team_elo_change = k * (1 - e1)
    losing_team_elo_change = k * (0 - e2)

    win_elo_diff = winning_team_elo - losing_team_elo
    lose_elo_diff = losing_team_elo - winning_team_elo

    print(f'Winning team Elo: {winning_team_elo}  Losing team Elo: {losing_team_elo}  '
          f'win change {winning_team_elo_change}  lose change {losing_team_elo_change}   '
          f'win elo diff {win_elo_diff}  lose elo diff {lose_elo_diff}')

    return winning_team_elo_change, losing_team_elo_change, win_elo_diff, lose_elo_diff


def apply_trueskill(team1, team2):
    # team1 is the Losing team

    team1_r = [player.trueskill for player in team1]
    team2_r = [player.trueskill for player in team2]

    team1_r_new, team2_r_new = standard_env.rate([team1_r, team2_r])

    game_quality = quality([team1_r, team2_r])
    print(game_quality)
    return game_quality, team1_r_new, team2_r_new


def apply_faction_trueskill(team1, team2, winning_facs, losing_facs):
    # team1 is the Losing team
    team1_r = []
    team2_r = []
    for player, faction in zip(team1, winning_facs):
        sub_fac = sub_faction_dict[faction]
        team1_r.append(player.return_faction_true(sub_fac))

    for player, faction in zip(team2, losing_facs):
        sub_fac = sub_faction_dict[faction]
        team2_r.append(player.return_faction_true(sub_fac))

    team1_r_new, team2_r_new = teams_env.rate([team1_r, team2_r])

    game_quality = quality([team1_r, team2_r])

    for player, faction, trues in zip(team1, winning_facs, team1_r_new):
        sub_fac = sub_faction_dict[faction]
        player.set_faction_true(sub_fac, trues)

    for player, faction, trues in zip(team2, losing_facs, team2_r_new):
        sub_fac = sub_faction_dict[faction]
        player.set_faction_true(sub_fac, trues)

    return game_quality


# object for holding doc win rates
faction_games = {}
for faction in faction_dict:
    faction_games[faction] = []

# hold games for game stats

companies_dict = {}

games_trueskill = []

for game in game_list[:]:
    key = game[0]
    Game = game[1]

    winning_team = []
    losing_team = []
    if datetime.datetime.strptime(Game.date, '%d/%m/%y') >= process_date:
        if Game.winner != 'Draw':
            if len(Game.players) > 2:
                companies_dict[Game] = {"Winning Team": {},
                                        "Losing Team:": {}}
                for player in Game.players:
                    if faction_dict[player[1]] == Game.winner:
                        winning_team.append((player[0], players[player[0]].totalElo, player[1]))
                        faction_games[player[1]].append(
                            [datetime.datetime.strptime(key[0], '%d/%m/%y'), "Win", players[player[0]].totalElo])
                    else:
                        # This guy Loses :(
                        losing_team.append((player[0], players[player[0]].totalElo, player[1]))
                        faction_games[player[1]].append(
                            [datetime.datetime.strptime(key[0], '%d/%m/%y'), "Loss", players[player[0]].totalElo])

                winning_team_elo = sum(winner[1] for winner in winning_team) / len(winning_team)
                losing_team_elo = sum(loser[1] for loser in losing_team) / len(winning_team)

                win_elo_change, lose_elo_change, win_elo_diff, lose_elo_diff = calc_elo(winning_team_elo,
                                                                                        losing_team_elo)

                # containers for trueskill objects
                team1 = []
                team2 = []
                winning_facs = []
                losing_facs = []
                for player in winning_team:
                    # companies_dict[Game]["Winning Team"][players[player[0]]] = players[player[5]]
                    all_comps[str(game[0])][player[0]]["ELO"] = players[player[0]].totalElo
                    all_comps[str(game[0])][player[0]]["WIN"] = True
                    t_elo = players[player[0]].totalElo
                    players[player[0]].eloAdd(win_elo_change)
                    players[player[0]].wins += 1
                    players[player[0]].eloDifference += win_elo_diff
                    players[player[0]].eloChanges.append(win_elo_diff)

                    winning_facs.append(player[2])

                    team1.append(players[player[0]])
                    fac = sub_faction_dict[player[2]]

                    fac_mu = players[player[0]].return_faction_true(fac).mu
                    fac_sig = players[player[0]].return_faction_true(fac).sigma

                    mu = players[player[0]].trueskill.mu
                    sigma = players[player[0]].trueskill.sigma

                    Game.factions["winners"].append(
                        [key, player[0], player[2], t_elo, "Victory", mu, sigma, fac_mu, fac_sig])

                for player in losing_team:
                    all_comps[str(game[0])][player[0]]["ELO"] = players[player[0]].totalElo
                    all_comps[str(game[0])][player[0]]["WIN"] = False
                    t_elo = players[player[0]].totalElo
                    players[player[0]].eloAdd(lose_elo_change)
                    players[player[0]].losses += 1
                    players[player[0]].eloDifference += lose_elo_diff
                    players[player[0]].eloChanges.append(lose_elo_diff)

                    losing_facs.append(player[2])

                    team2.append(players[player[0]])
                    fac = sub_faction_dict[player[2]]

                    fac_mu = players[player[0]].return_faction_true(fac).mu
                    fac_sig = players[player[0]].return_faction_true(fac).sigma

                    mu = players[player[0]].trueskill.mu
                    sigma = players[player[0]].trueskill.sigma

                    Game.factions["losers"].append(
                        [key, player[0], player[2], t_elo, "Defeat", mu, sigma, fac_mu, fac_sig])

                # Trial Trueskill
                game_quality, team1r, team2r = apply_trueskill(team1, team2)
                game_quality_team = apply_faction_trueskill(team1, team2, winning_facs, losing_facs)
                for i, player in enumerate(team1):
                    player.trueskill = team1r[i]
                for i, player in enumerate(team2):
                    player.trueskill = team2r[i]

past_x_games = 30

player_list = [(player,
                players[player].trueskill.mu,
                players[player].trueskill.sigma,
                players[player].totalElo,
                players[player].wins,
                players[player].losses,
                players[player].wins / (players[player].wins + players[player].losses),
                players[player].eloDifference / (players[player].wins + players[player].losses),
                sum(players[player].eloChanges[:past_x_games]) / past_x_games) for player in players if
               players[player].wins + players[player].losses > 0]

player_list.sort(key=lambda x: x[1])

player_table = pd.read_csv("G:/New folder/players_table.csv")

player_table["profile"] = player_table["profile"].apply(real_name)

p_df = pd.DataFrame(player_list,
                    columns=["NAME", "MU", "SIGMA", "ELO", "WINS", "LOSSES", "RATIO", "AVERAGE_STACK", "RECENT_STACK"])
p_df["GAMES"] = p_df["WINS"] + p_df["LOSSES"]
f_df = pd.read_csv('players_table.csv')
f_df = f_df.drop_duplicates(subset=['ID_MEMBER', 'profile'])


def match_to_forum(player_name):
    print(player_name)
    test = f_df[f_df["profile"].str.upper() == player_name.upper()]["ID_MEMBER"]
    f_ids = []
    if len(test) > 0:
        f_ids += list(test)
        try:
            s_name = smurfs.loc[player_name]["REAL_NAME"]
            print(s_name)
            test = f_df[f_df["profile"].str.upper() == s_name]["ID_MEMBER"]
            if len(test) > 0:
                f_ids += list(test)
        except KeyError:
            pass

    return f_ids


p_df_rows = []
for i, row in p_df.iterrows():
    name_to_check = row["NAME"]
    ids = match_to_forum(name_to_check)
    if len(ids) > 0:
        print(ids)
        for id in ids:
            current_row = row.copy()
            current_row["ID_MEMBER"] = id
            p_df_rows.append(current_row)
    else:
        p_df_rows.append(row)

p_df = pd.DataFrame(p_df_rows)
p_df = p_df.drop_duplicates()
p_df.index.name = 'ID'


def normalise_to_elo(mu, old_min, old_max):
    new_min = 1000
    new_max = 2000
    return ((mu - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min


old_min, old_max = p_df["MU"].min(), p_df["MU"].max()
old_min_sig, old_max_sig = p_df["SIGMA"].min(), p_df["SIGMA"].max()
p_df["MU"] = p_df["MU"].apply(normalise_to_elo, args=(old_min, old_max))
keep_cols = ['NAME', 'MU', 'ID_MEMBER', "GAMES", 'SIGMA']
p_df.to_csv('players.csv')
p_df[keep_cols].to_csv('players_upload.csv')

master_df = pd.DataFrame(columns=['Date', 'Victory', 'ELO', 'Faction'])

for faction_name in faction_games:
    df = pd.DataFrame(faction_games[faction_name], columns=['Date', 'Victory', 'ELO'])
    df['Faction'] = faction_name
    master_df = master_df.append(df)

master_df.to_csv('file.csv')

faction_stats = []

player_elos = []

games_list = []

for game in game_list:
    Game = game[1]
    if datetime.datetime.strptime(Game.date, '%d/%m/%y') >= process_date:
        if Game.winner != 'Draw':
            if len(Game.players) > 2:
                for side in Game.factions:
                    for player in Game.factions[side]:
                        faction_stats.append(player)
                        player_elos.append([Game.date,
                                            Game.id,
                                            player[1],  # name
                                            player[3],
                                            player[2],  # facxtion,
                                            player[5],  # mu
                                            player[6],  # sigma
                                            Game.winner,
                                            player[7],  # FAC MY
                                            player[8]])  # FAC SIGFMA

                if Game.winner == 'Allies':
                    allies = Game.factions['winners']
                    axis = Game.factions['losers']
                else:
                    axis = Game.factions['winners']
                    allies = Game.factions['losers']
                games_list.append(Game.winner)

player_elos_df = pd.DataFrame(player_elos)
# 27/03/2019	170	UKPOWERMAX	1500	OMGUPG.CMW.ROYALENGIESDOC	25	8.333333333	Allies
player_elos_df.columns = ['Date', 'Game-ID', 'Player', 'ELO', 'Doctrine', 'MU', 'SIGMA', 'Winner', 'FAC_MU',
                          'FAC_SIGMA']
player_elos_df['MU'] = player_elos_df['MU'].apply(normalise_to_elo, args=(old_min, old_max))

# player_elos_df['FAC_MU'] = player_elos_df['FAC_MU'].apply(normalise_to_elo,args=(old_min,old_max))

player_elos_df.to_csv('player_elos_over_time.csv')
faction_df = pd.DataFrame(faction_stats)
# ('27/03/19', 170)	UKPOWERMAX	OMGUPG.CMW.ROYALENGIESDOC	1500	Victory	25	8.333333333

faction_df.columns = ['Date-Game-ID', 'Player', 'Doctrine', 'ELO', 'Winner', 'MU', 'SIGMA', 'FAC_MU', 'FAC_SIGMA']
faction_df['MU'] = faction_df['MU'].apply(normalise_to_elo, args=(old_min, old_max))
# old_min,old_max = player_elos_df['FAC_MU'].min(), player_elos_df['FAC_MU'].max()
faction_df['FAC_MU'] = faction_df['FAC_MU'].apply(normalise_to_elo, args=(old_min, old_max))

for faction in faction_dict:
    # print(faction)
    games = faction_games[faction]

faction_df.to_csv('factionstats.csv')

player_list = []

for player in players:
    player_list.append([player, players[player]])

axisWins = 0
alliedWins = 0

gameListTemp = []

superstring = json.dumps(all_comps)

text_file = open("companies.json", "w")
text_file.write(superstring)
text_file.close()

p_fac_list = []
for player in player_list:
    for fac in ["ALLY", "CMW", "AXIS", "PE"]:
        p_fac_list.append([player[0],  # name
                           fac,  # faction
                           player[1].return_faction_true(fac).mu,
                           player[1].return_faction_true(fac).sigma])

pfdf = pd.DataFrame(p_fac_list, columns=["NAME", "FACTION", "MU", "SIGMA"])
old_min, old_max = pfdf["MU"].min(), pfdf["MU"].max()
pfdf['MU'] = pfdf['MU'].apply(normalise_to_elo, args=(old_min, old_max))
pfdf.to_csv('players_faction_ratings.csv')
