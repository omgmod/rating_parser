Use `trueskill` python package
* Initialize Trueskill environment with draw probability = 0

Smurf dictionary CSV to normalize player names

Game
* id
* date
* winner
* map
* players list of (player name, faction)
* factions dict of winner and loser lists

Player
* games dict
* wins
* losses
* allied wins
* allied losses
* axis wins
* axis losses
* total elo
* allied elo
* axis elo
* trueskill Rating
* faction Ratings
* elo difference
* elo changes


For a list of battle reports:
1. Get battle id
2. Get side winner
3. Get players
4. Get time elapsed
5. If battle time < 15min and dropped players exist, skip
6. If game was reported already, skip
7. Otherwise, create a Game object with the id, date, winner, map

Result is a game list of games with start date after 1/1/19
Dictionary of name to Player object with default ELO/TS Rating

1. Parse a list of companies from the battle report
2. Get datetime of the battle report time
3. Get datetime of the battle report time - 1 day
4. Get battle id
5. For each player name, get normalized non-smurf name
6. Get company for player
7. Create player name list of tuples of (player name, faction)
8. Find the Game for this battle id and date, add the player list to the Game
9. If couldn't find a Game for this battle id and date, try with the -1 day date

### Elo Calculation per Game
#### For the list of Games
* With winner != `Draw`
* With players > 2

#### For each Player
1. If the Player was on the winning side, append a tuple to the winning players list of
   (name, total elo, side)
2. Otherwise append a tuple to the losing team list with (name, total elo, side)

Elo comes from the players dict to Player

#### Battle
##### ELO
1. Get the mean winning team ELO
2. Get the mean losing team ELO
3. Calculate the winning team ELO change and the losing team ELO change

For players on the winning team
1. Add the winning team ELO change to the player's totalElo
2. Add a win
3. Add the winning ELO diff to the player's eloDifference
4. Add the winning ELO diff to the player's elo changes list

For players on the losing team
1. Add the losing team ELO change to the player's totalElo
2. Add a win
3. Add the losing ELO diff to the player's eloDifference
4. Add the losing ELO diff to the player's elo changes list

##### Trueskill
For players on the winning team
1. Get Player TS mu, sigma, factional mu, factional sigma
2. Add tuple to Game's winners list
3. Add to list of winning Players

For players on the losing team
1. Get Player TS mu, sigma, factional mu, factional sigma
2. Add tuple to Game's losers list
3. Add to list of losing Players

Apply Trueskill to the lists of winning and losing teams
1. Create lists of winning player Rating and losing player Rating
2. Using the standard Trueskill environment, rate the winning and losing teams
3. Get Trueskill game quality for the winning team Ratings and losing team Ratings
4. Return Game Quality, team 1 new Ratings, team 2 new Ratings

Apply Trueskill to Player's factional Rating
1. Create lists of Player factional Rating
2. Use the teams environment, rate the winning and losing teams
3. Get game quality for the rating
4. Set the Player's factional Rating to the new factional rating


1. Find the min and max mu of the calculated player ratings
2. Find the min and max sigma of the calculated player ratings
3. Apply normalization function to all player mu using the min and max mu
###### Normalize to ELO
1. With new min 1000 and new max 2000
2. Return ((mu - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min

### Output
Return 
* Player name
* mu
* sigma
* ID_MEMBER
* Games count

