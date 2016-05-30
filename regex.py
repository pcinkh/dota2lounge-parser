import urllib.request
import re
from datetime import datetime, timedelta

from pymongo import MongoClient



PARSE_SITE_URL = 'http://dota2lounge.com/'

HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
}

client = MongoClient('mongodb://localhost:27017/')
db = client.d2l_reg


regex = {
    'games': r'<div class="matchmain">(.*?)</div></div></div>',
    'live': r'(LIVE)',
    'time': r'<div class="whenm">([0-9]+)(\s)(\w+)',
    'match_id': r'<a href="match\?m=([0-9]+)',
    'teams': r'<div class="team"(.*?)</div>    </div>',
    'team_name': r'<div class="teamtext"><b>(.*?)</b>',
    'won': r'(won.png)',
}

req = urllib.request.Request(PARSE_SITE_URL, headers=HEADER)


def split_page(source, start, end):
    return source.split(start)[1].split(end)[0]


def get_time(value, unit):
    value = int(value)

    if 'second' in unit:
        return(datetime.utcnow() - timedelta(seconds=value))
    if 'minute' in unit:
        return(datetime.utcnow() - timedelta(minutes=value))
    if 'hour' in unit:
        return(datetime.utcnow() - timedelta(hours=value))
    if 'day' in unit:
        return(datetime.utcnow() - timedelta(days=value))


def parse_game(game):
    parsed_game = {}

    time_regex = re.findall(re.compile(regex['time']), game)
    time_list = list(time_regex[0])
    del time_list[1]

    parsed_game['time'] = get_time(time_list[0], time_list[1])

    parsed_game['match_id'] = re.findall(re.compile(regex['match_id']), game)

    team = re.findall(re.compile(regex['teams']), game)

    parsed_game['team_1'] = re.findall(re.compile(regex['team_name']), team[0])

    parsed_game['team_2'] = re.findall(re.compile(regex['team_name']), team[1])

    parsed_game['won'] = 0

    if re.findall(re.compile(regex['won']), team[0]):
        parsed_game['won'] = 1
    elif re.findall(re.compile(regex['won']), team[1]):
        parsed_game['won'] = 2

    return parsed_game


def mongo_save(game):
    games = db.games
    if not db.games.find_one({'match_id': game['match_id']}):
        games.insert_one(game)
    print(game)

with urllib.request.urlopen(req) as response:
    html = response.read().decode().replace('\n', '').replace('\r', '')

    games = split_page(
        html,
        '<article class="standard" id="bets" style="margin-top: 40px;">',
        '</article>'
    )

    games_list = re.findall(re.compile(regex['games']), games)

    for game in games_list:
        live = re.search(re.compile(regex['live']), game)

        if not live:
            mongo_save(parse_game(game))
