import regex
from datetime import datetime, timedelta

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import requests


SITE_URL = 'http://dota2lounge.com/'


client = MongoClient('mongodb://localhost:27017/')
db = client.d2l_reg


rgx = {
    'time': regex.compile(
        r'<div\sclass="whenm">(\d+?)\s([a-z]+?)\s'
    ),
    'match_id': regex.compile(
        r'<a\shref="match\?m=(\d+?)\"'
    ),
    'teams': regex.compile(
        r'<div\sclass="team"(.+?)</i></div>',
        regex.MULTILINE | regex.DOTALL
    ),
    'team_name': regex.compile(
        r'<div\sclass="teamtext"><b>(.+?)</b>'
    )
}


def main():
    html = requests.get(SITE_URL).text

    games = split_page(
        html,
        '<article class="standard" id="bets" style="margin-top: 40px;">',
        '</article>'
    )

    games_list = games.split('<div class="matchheader">')

    for game in games_list[1:]:
        if 'LIVE' not in game and 'from now' not in game:
            mongo_save(parse_game(game))


def split_page(source, start, end):
    return source.split(start)[1].split(end)[0]


def get_time(value, unit):
    value = int(value)

    params = {}

    for ident, param in (
        ('second', 'seconds'),
        ('minute', 'minutes'),
        ('hour', 'hours'),
        ('day', 'days')
    ):
        if ident in unit:
            params[param] = value
            break

    if not params:
        raise NotImplementedError

    return datetime.utcnow() - timedelta(**params)


def parse_game(game):
    parsed_game = {}

    time_regex = regex.findall(rgx['time'], game)
    time_list = list(time_regex[0])

    parsed_game['time'] = get_time(time_list[0], time_list[1])

    parsed_game['_id'] = int(regex.findall(rgx['match_id'], game)[0])

    team = regex.findall(rgx['teams'], game)

    parsed_game['team_1'] = regex.findall(rgx['team_name'], team[0])[0]

    parsed_game['team_2'] = regex.findall(rgx['team_name'], team[1])[0]

    if 'won.png' in team[0]:
        parsed_game['won'] = 1
    elif 'won.png' in team[1]:
        parsed_game['won'] = 2
    else:
        parsed_game['won'] = 0

    return parsed_game


def mongo_save(game):
    try:
        db.games.insert_one(game)
    except DuplicateKeyError:
        pass
    else:
        print(game)

if __name__ == '__main__':
    main()