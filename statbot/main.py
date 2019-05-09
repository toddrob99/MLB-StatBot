#!/usr/bin/env python
# encoding=utf-8
"""
# MLB Stat Bot

Created by Todd Roberts

https://github.com/toddrob99/MLB-StatBot
"""
import sys
if sys.version_info.major < 3:
    reload(sys)
    sys.setdefaultencoding('utf8')
# Trying to support Python 2.7

import version
__version__ = version.VERSION
"""Installed version of MLB-StatBot"""

from datetime import datetime,timedelta
import time
import statsapi
import praw
import os
import sqlite3
import requests

class StatBot:
    def __init__(self,sub):
        self.sub = sub
        self.replyFooter = '\n\n^^I ^^am ^^a ^^bot. ^^Not ^^affiliated ^^with ^^MLB. ^^Downvoted ^^replies ^^will ^^be ^^deleted. ^^[[source/doc](https://github.com/toddrob99/MLB-StatBot)] ^^[[feedback](https://np.reddit.com/message/compose?to=toddrob&subject=mlb-bot&message=)]'
        self.del_threshold = -2
        self.pause_after = 5
        self.comments = {}
        print('StatBot starting up...')
        reddit_clientId = None
        reddit_clientSecret = None
        reddit_refreshToken = None

        while not reddit_clientId and not reddit_clientSecret and not reddit_refreshToken:
            try:
                import auth
                reddit_clientId = auth.reddit_clientId
                reddit_clientSecret = auth.reddit_clientSecret
                reddit_refreshToken = auth.reddit_refreshToken
            except Exception as e:
                print('Error importing authentication info from auth.py: {}'.format(e))
            if reddit_clientId and reddit_clientSecret and reddit_refreshToken: continue
            print('Reddit API authentication data not found. Let\'s fix that.')
            if input('Do you already have a client id, client secret, and refresh token? (Y/N) ').lower() == 'y':
                reddit_clientId = input('Enter client id: ')
                reddit_clientSecret = input('Enter client secret: ')
                reddit_refreshToken = input('Enter refresh token: ')
            else:
                print('Log in to Reddit as your bot user in your default browser, go to https://www.reddit.com/prefs/apps, click the "are you a developer? create an app" button, ')
                print('and complete the form using http://localhost:8080 as the redirect uri. These fields can be changed later if needed.')
                reddit_clientId = input('Enter client id (listed under your app name): ')
                reddit_clientSecret = input('Enter client secret: ')
                print('Your web browser will now open and take you to a Reddit authorization page. Ensure you are logged in as your bot user and click allow.')
                r = praw.Reddit(client_id=reddit_clientId,
                                client_secret=reddit_clientSecret,
                                redirect_uri='http://localhost:8080',
                                user_agent='MLB-StatBot by Todd Roberts'+__version__)
                import webbrowser
                url = r.auth.url(['identity', 'submit', 'edit', 'read'], '...', 'permanent')
                print('Here is the URL in case you need to copy/paste into your browser: {}'.format(url))
                webbrowser.open(url)
                reddit_authCode = input('Enter the code from the address bar of your browser, everything after code=')
                reddit_refreshToken = r.auth.authorize(reddit_authCode)
                try:
                    f = open(os.path.dirname(os.path.realpath(__file__)) + '/auth.py', 'w+')
                    f.write("#!/usr/bin/env python\nreddit_clientId='{}'\nreddit_clientSecret='{}'\nreddit_refreshToken='{}'\n".format(reddit_clientId,reddit_clientSecret,reddit_refreshToken))
                    f.close()
                except Exception as e:
                    print('Error writing authentication info to auth.py: {}'.format(e))

            try:
                f = open(os.path.dirname(os.path.realpath(__file__)) + '/auth.py', 'w+')
                f.write("#!/usr/bin/env python\nreddit_clientId='{}'\nreddit_clientSecret='{}'\nreddit_refreshToken='{}'\n".format(reddit_clientId,reddit_clientSecret,reddit_refreshToken))
                f.close()
            except Exception as e:
                print('Error writing authentication info to auth.py: {}'.format(e))

        print('Initializing Reddit API with user agent MLB-StatBot by Todd Roberts {}'.format(__version__))
        try:
            self.r = praw.Reddit(client_id=reddit_clientId,
                                 client_secret=reddit_clientSecret,
                                 refresh_token=reddit_refreshToken,
                                 user_agent='MLB-StatBot by Todd Roberts'+__version__)
        except Exception as e:
            print('Error authenticating with Reddit. Please check the values in auth.py and try again. Error message: {}'.format(e))
        try:
            if 'identity' in self.r.auth.scopes():
                print('Authorized Reddit user: {}'.format(self.r.user.me()))
        except Exception as e:
            print('Reddit authentication failure. Please check the values in auth.py and try again. Error message: {}'.format(e))

        try:
            self.db = sqlite3.connect(os.path.dirname(os.path.realpath(__file__)) + '/statbot.db')
            #self.db.set_trace_callback(print)
            """Local sqlite database to store info about processed comments"""
        except sqlite3.Error as e:
            print('Error connecting to database: {}'.format(e))
            return None

        self.dbc = self.db.cursor()
        self.dbc.execute('''CREATE TABLE IF NOT EXISTS comments (
                            comment_id text PRIMARY KEY,
                            sub text NOT NULL,
                            author text NOT NULL,
                            post text NOT NULL,
                            date text NOT NULL,
                            cmd text,
                            errors text,
                            reply text,
                            removed integer,
                            score integer
                        );''')
        self.db.commit()

    def __del__(self):
        try:
            print('Closing DB connection.')
            self.db.close()
        except sqlite3.Error as e:
            print('Error closing database connection: {}'.format(e))

    def run(self):
        self.dbc.execute('SELECT comment_id,date,reply FROM comments ORDER BY date DESC LIMIT 500;')
        comment_ids = self.dbc.fetchall()
        for cid in comment_ids:
            self.comments.update({cid[0] : {'date' : cid[1], 'reply' : cid[2], 'historical' : True}})

        while True:
            print('Monitoring comments in the following subreddit(s): {}...'.format(self.sub))
            for comment in self.r.subreddit(self.sub).stream.comments(pause_after=self.pause_after):
                if not comment:
                    break #take a break to delete downvoted replies
                if comment.id in self.comments.keys():
                    print('Already processed comment {}'.format(comment.id))
                    continue
                replyText = ''
                if str(self.r.user.me()).lower() in comment.body.lower() and comment.author != self.r.user.me():
                    self.comments.update({comment.id : {'sub' : comment.subreddit, 'author' : comment.author, 'post' : comment.submission, 'date' : time.time(), 'cmd' : [], 'errors' : []}})
                    self.dbc.execute("insert or ignore into comments (comment_id, sub, author, post, date) values (?, ?, ?, ?, ?);", (str(comment.id), str(comment.subreddit), str(comment.author), str(comment.submission), str(comment.created_utc)))
                    print('({}) {} - {}: {}'.format(comment.subreddit, comment.id, comment.author, comment.body))
                    if 'help' in comment.body.lower():
                        self.comments[comment.id]['cmd'].append('help')
                        replyText += 'Invoke me by including my name anywhere in your comment.\n\n'
                        replyText += 'Include an available command in your comment: [help, score, careerstats, seasonstats, standings, winprob], '
                        replyText += 'along with the subject in curly brackets.\n\n'
                        replyText += 'For stats commands, you can also include the type: [hitting, pitching, fielding].\n\n'
                        replyText += 'For example, `careerstats {hamels} pitching` or `score {phillies}` or `standings {nle}` '
                        replyText += '(try including the word wildcard when asking for standings).\n\n'
                        replyText += 'I am currently monitoring the following subreddit(s): ' + self.sub + '.'
                    if 'seasonstats' in comment.body.lower():
                        self.comments[comment.id]['cmd'].append('seasonstats')
                        if replyText != '': replyText += '\n\n*****\n\n'
                        try:
                            who = statsapi.lookup_player(comment.body[comment.body.find('{')+1:comment.body.find('}')])[0]['id']
                            what = []
                            if 'hitting' in comment.body.lower() or 'batting' in comment.body.lower(): what.append('hitting')
                            if 'pitching' in comment.body.lower(): what.append('pitching')
                            if 'fielding' in comment.body.lower(): what.append('fielding') 
                            if len(what):
                                stats = statsapi.player_stats(who,str(what).replace('\'','').replace(' ',''),'season')
                            else:
                                stats = statsapi.player_stats(who,type='season')
                            replyText += '\n    ' + stats.replace('\n','\n    ')
                        except Exception as e:
                            print('Error generating response for seasonstats: {}'.format(e))
                            self.comments[comment.id]['errors'].append('Error generating response for seasonstats: {}'.format(e))
                    if 'careerstats' in comment.body.lower():
                        self.comments[comment.id]['cmd'].append('careerstats')
                        if replyText != '': replyText += '\n\n*****\n\n'
                        try:
                            who = self.lookup_player(comment.body[comment.body.find('{')+1:comment.body.find('}')])
                            what = []
                            if 'hitting' in comment.body.lower() or 'batting' in comment.body.lower(): what.append('hitting')
                            if 'pitching' in comment.body.lower(): what.append('pitching')
                            if 'fielding' in comment.body.lower(): what.append('fielding') 
                            if len(what):
                                stats = statsapi.player_stats(who,str(what).replace('\'','').replace(' ',''),'career')
                            else:
                                stats = statsapi.player_stats(who,type='career')
                            replyText += '\n    ' + stats.replace('\n','\n    ')
                        except Exception as e:
                            print('Error generating response for careerstats: {}'.format(e))
                            self.comments[comment.id]['errors'].append('Error generating response for careerstats: {}'.format(e))
                    if 'nextgame' in comment.body.lower():
                        self.comments[comment.id]['cmd'].append('nextgame')
                        if replyText != '': replyText += '\n\n*****\n\n'
                        try:
                            who = statsapi.lookup_team(comment.body[comment.body.find('{')+1:comment.body.find('}')])[0]['id']
                            next = statsapi.next_game(who)
                            game = statsapi.schedule(game_id=next)
                            replyText += game[0]['summary']
                        except Exception as e:
                            print('Error generating response for nextgame: {}'.format(e))
                            self.comments[comment.id]['errors'].append('Error generating response for nextgame: {}'.format(e))
                    if 'lastgame' in comment.body.lower():
                        self.comments[comment.id]['cmd'].append('lastgame')
                        if replyText != '': replyText += '\n\n*****\n\n'
                        try:
                            who = statsapi.lookup_team(comment.body[comment.body.find('{')+1:comment.body.find('}')])[0]['id']
                            last = statsapi.last_game(who)
                            game = statsapi.schedule(game_id=last)
                            replyText += game[0]['summary']
                        except Exception as e:
                            print('Error generating response for lastgame: {}'.format(e))
                            self.comments[comment.id]['errors'].append('Error generating response for lastgame: {}'.format(e))
                    if 'winprob' in comment.body.lower():
                        self.comments[comment.id]['cmd'].append('winprob')
                        if replyText != '': replyText += '\n\n*****\n\n'
                        try:
                            who = statsapi.lookup_team(comment.body[comment.body.find('{')+1:comment.body.find('}')])[0]['id']
                            game = statsapi.schedule(team=who)[0]
                            contextMetrics = statsapi.get('game_contextMetrics',{'gamePk':game['game_id']})
                            away_win_prob = contextMetrics.get('awayWinProbability','-')
                            home_win_prob = contextMetrics.get('homeWinProbability','-')
                            replyText += '\n    ' + game['summary'] + '\n'
                            replyText += '    Current win probabilities: ' + game['away_name'] + ' ' + str(away_win_prob) + '%, ' + game['home_name'] + ' ' + str(home_win_prob) + '%'
                        except Exception as e:
                            print('Error generating response for winprob: {}'.format(e))
                            self.comments[comment.id]['errors'].append('Error generating response for winprob: {}'.format(e))
                    if 'score' in comment.body.lower() and 'Current win probabilities' not in replyText:
                        self.comments[comment.id]['cmd'].append('score')
                        if replyText != '': replyText += '\n\n*****\n\n'
                        try:
                            who = comment.body[comment.body.find('{')+1:comment.body.find('}')].lower()
                            if who in ['nle','nlw','nlc','ale','alw','alc','all']:
                                todaysGames = statsapi.get('schedule',{'fields':'dates,date,games,gamePk,teams,away,team,division,abbreviation','sportId':1,'hydrate':'team(division)'})
                                gamePks = ''
                                for i in (x['gamePk'] for x in todaysGames['dates'][0]['games'] if who == 'all' or x['teams']['away']['team']['division']['abbreviation'].lower() == who or x['teams']['home']['team']['division']['abbreviation'].lower() == who):
                                    gamePks += '{},'.format(i)
                                if len(gamePks):
                                    if gamePks[-1] == ',': gamePks = gamePks[:-1]
                                games = statsapi.schedule(game_id=gamePks)
                                for game in games:
                                    replyText += '\n    ' + game['summary']
                            else:
                                who = statsapi.lookup_team(comment.body[comment.body.find('{')+1:comment.body.find('}')])[0]['id']
                                game = statsapi.schedule(team=who)
                                replyText += game[0]['summary']
                        except Exception as e:
                            print('Error generating response for score: {}'.format(e))
                            self.comments[comment.id]['errors'].append('Error generating response for score: {}'.format(e))
                    if 'standings' in comment.body.lower():
                        self.comments[comment.id]['cmd'].append('standings')
                        if replyText != '': replyText += '\n\n*****\n\n'
                        try:
                            if comment.body.find('{') != -1:
                                who = comment.body[comment.body.find('{')+1:comment.body.find('}')].lower()
                            else: who='all'
                            wc = True if any(True for x in ['wc','wildcard','wild card'] if x in comment.body) else False
                            if who == 'all':
                                standings = statsapi.standings(date=datetime.today().strftime('%m/%d/%Y'),include_wildcard=wc)
                            elif who in ['nle','nlw','nlc','ale','alw','alc']:
                                standings = statsapi.standings(date=datetime.today().strftime('%m/%d/%Y'),division=who,include_wildcard=wc)
                            elif who in ['nl','al']:
                                leagueId = 103 if who=='al' else 104
                                standings = statsapi.standings(leagueId=leagueId,date=datetime.today().strftime('%m/%d/%Y'),include_wildcard=wc)
                            replyText += '\n    {}'.format(standings.replace('\n','\n    '))
                        except Exception as e:
                            print('Error generating response for standings: {}'.format(e))
                            self.comments[comment.id]['errors'].append('Error generating response for standings: {}'.format(e))

                    if replyText != '':
                        try:
                            latest_reply = comment.reply(replyText + self.replyFooter)
                            self.comments[comment.id].update({'reply' : latest_reply})
                            latest_reply.disable_inbox_replies()
                            print('Replied with comment id {} and disabled inbox replies.'.format(latest_reply))
                            self.dbc.execute("update comments set cmd=?,reply=? where comment_id=?;", (str(self.comments[comment.id]['cmd']), str(latest_reply), str(comment.id)))
                        except Exception as e:
                            print('Error replying to comment or disabling inbox replies: {}'.format(e))
                            self.comments[comment.id]['errors'].append('Error submitting comment or disabling inbox replies: {}'.format(e))

                    if len(self.comments[comment.id].get('errors')):
                        self.dbc.execute("update comments set errors=? where comment_id=?;", (str(self.comments[comment.id].get('errors')), str(comment.id)))
                    self.db.commit()

            print('Checking for downvotes on {} replies...'.format(sum(1 for x in self.comments if self.comments[x].get('reply') and not self.comments[x].get('removed') and not self.comments[x].get('historical'))))
            for x in (x for x in self.comments if self.comments[x].get('reply') and not self.comments[x].get('removed') and not self.comments[x].get('historical')):
                if self.comments[x]['reply'].score <= self.del_threshold:
                    print('Deleting comment {} with score ({}) at or below threshold ({})...'.format(self.comments[x]['reply'], self.comments[x]['reply'].score, self.del_threshold))
                    try:
                        self.comments[x]['reply'].delete()
                        self.comments[x].update({'removed':time.time()})
                        self.dbc.execute("update comments set removed=? where comment_id=?;", (str(self.comments[x].get('removed')), str(x)))
                    except Exception as e:
                        print('Error deleting downvoted comment: {}'.format(e))
                        self.comments[x]['errors'].append('Error deleting downvoted comment: {}'.format(e))
            self.db.commit()

        return

    def lookup_player(self, keyword):
        """Check statsapi.lookup_player() and if no results, try other MLB source.
        Stats API only returns active players.
        """
        players = statsapi.lookup_player(keyword)
        if len(players): return players[0]['id']
        else:
            r = requests.get('http://lookup-service-prod.mlb.com/json/named.search_player_all.bam?sport_code=%27mlb%27&name_part=%27{}%25%27'.format(keyword))
            if r.status_code not in [200,201]:
                print('Error looking up player from alternate MLB source. Status code: {}.'.format(r.status_code))
                return ''
            else:
                return r.json()['search_player_all']['queryResults']['row']['player_id'] if r.json()['search_player_all']['queryResults']['totalSize']=='1' else r.json()['search_player_all']['queryResults']['row'][0]['player_id']

if __name__=='__main__':
    if len(sys.argv)>1:
        sub = sys.argv[1]
    else:
        sub= input('What subreddit(s) should I monitor? (Include multiple in the format sub1+sub2+sub3): ')
    mlbbot = StatBot(sub)
    mlbbot.run()
