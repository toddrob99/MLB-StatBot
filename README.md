# MLB-StatBot

Python script that replies to comments in configured subreddits with MLB data.

This project was developed in Python 3.7, but should also work with Python 2.7.

## Setup

Install praw and MLB-StatsAPI:

`pip install praw`
`pip install MLB-StatsAPI`

Run statbot\main.py in Python and either pass the subreddit(s) as a parameter or enter when prompted.

`py -3 statbot\main.py MySubreddit`

If you want to monitor multiple subreddits, separate them with +.

`py -3 statbot\main.py MySubreddit+MyOtherSub`

The first time you run the bot, you will be asked if you already have Reddit authentication information. 
If so, enter Y and then paste the info as requested. If not, enter N and follow the prompts.

Your Reddit authentication info will be stored in statbot\auth.py, and you can edit it there if needed.

## Use

Invoke the bot in a monitored subreddit by including the bot's reddit username in a comment. 

Include a command, subject, and qualifier as needed, and the bot will reply with the requested data.

Downvoted replies will be deleted automatically.

## Commands

### help
Subject: None

Qualifier: None

Reply: Information about using the bot, including a list of commands.

Example: `botname help`

### careerstats
Subject: Player name, enclosed in {} anywhere in your comment. Can be part of first name, last name, or full name in format 'Last, First'. Include enough for the bot to uniquely identify a single player, or you might not get the result you expect. For example, Aaron Nola's last name is part of Nolan Arenado's first name, so in order to get stats for Aaron Nola, try {nola,} (enough of 'last, first' format to be unique).

Qualifier: Type of stats requested, anywhere in your comment. Available values: hitting/batting, pitching, and fielding. Include multiple types if you wish, or leave out the qualifier to return all available.

Reply: The given player's career stats of the type(s) requested. If the player fielded in multiple positions, there will be separate sections in the reply for each position.

Example: `botname careerstats {nola,} pitching`

### seasonstats
Subject: Player name, enclosed in {} anywhere in your comment. Can be part of first name, last name, or full name in format 'Last, First'. Include enough for the bot to uniquely identify a single player, or you might not get the result you expect. For example, Aaron Nola's last name is part of Nolan Arenado's first name, so in order to get stats for Aaron Nola, try {nola,} (enough of 'last, first' format to be unique).

Qualifier: Type of stats requested, anywhere in your comment. Available values: hitting/batting, pitching, and fielding. Include multiple types if you wish, or leave out the qualifier to return all available.

Reply: The given player's career stats of the type(s) requested. If the player fielded in multiple positions, there will be separate sections in the reply for each position.

Example: `botname seasonstats {hoskins} batting`

### score
Subject: Team or division, enclosed within {} anyhwere in your comment. Can be part of the team's name, location, or team code. Include enough characters to uniquely identify a team. For example, 'lad' will return PhiLADelphia and not LA Dodgers as you might expect. To return scores for any games for a given division, include the abbreviation (nle, alw, etc.).

Qualifier: None

Reply: A summary of requested games, including teams, scores if game is in progress or final, inning if game is in progress, and status.

Example: `botname score {nle}` or `botname score {phillies}

### standings
Subject: Division or league, enclosed within {} anywhere in your comment. Leave out for all divisions in both leagues. Include abbreviation for the league/division you want, for example {nl} or {alw}.

Qualifier: Include `wildcard` or `wc` in your comment if you want wildcard standings to be included in the reply. 

Reply: Division standings for the requested division/league(s), including wildcard standings if qualifier is present.

Example: `botname standings {nle}` or `botname standings {al} wildcard`

### nextgame
Subject: Team name, enclosed in {} anywhere in your comment. Can be part of the team's name, location, or team code. Include enough characters to uniquely identify a team. For example, 'lad' will return PhiLADelphia and not LA Dodgers as you might expect. To return scores for any games for a given division, include the abbreviation (nle, alw, etc.).

Qualifier: None

Reply: Summary information about the given team's next game, including team names, scores if game is in progress or final, inning if game is in progress, and status.

Example: `botname nextgame {oakland}`

Note: The MLB API seems to get confused and return an unexpected game when requesting the next or previous game. This is how the API is returning the data, and there is nothing I can easily do to make this work better.

### lastgame
Subject: Team name, enclosed in {} anywhere in your comment. Can be part of the team's name, location, or team code. Include enough characters to uniquely identify a team. For example, 'lad' will return PhiLADelphia and not LA Dodgers as you might expect. To return scores for any games for a given division, include the abbreviation (nle, alw, etc.).

Qualifier: None

Reply: Summary information about the given team's last game, including team names, scores if game is in progress or final, inning if game is in progress, and status.

Example: `botname lastgame {cubs}`

Note: The MLB API seems to get confused and return an unexpected game when requesting the next or previous game. This is how the API is returning the data, and there is nothing I can easily do to make this work better.

### winprob
Subject: Team name, enclosed in {} anywhere in your comment. Can be part of the team's name, location, or team code. Include enough characters to uniquely identify a team. For example, 'lad' will return PhiLADelphia and not LA Dodgers as you might expect. To return scores for any games for a given division, include the abbreviation (nle, alw, etc.).

Qualifier: None

Reply: Game summary information, as well as current win probabilities for both teams. Works best while the team has a game in progress.

Example: `botname winprob {phi}`

## Copyright Notice

This package and its author are not affiliated with MLB or any MLB team. This project uses the MLB-StatsAPI and PRAW packages to interface with the MLB and Reddit APIs. Use of MLB data is subject to the notice posted at http://gdx.mlb.com/components/copyright.txt.
