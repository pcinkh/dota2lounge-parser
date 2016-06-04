import regex
from datetime import datetime, timedelta

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import requests


SITE_URL = 'http://dota2lounge.com/'


client = MongoClient('mongodb://localhost:27017/')
db = client.d2l_reg


rgx = {
    'games': regex.compile(
        r'<div class="matchmain">(.*?)</div>\r\n</div>\r\n</div>',
        regex.MULTILINE | regex.DOTALL
    ),
    'live': regex.compile(
        r'(LIVE)',
        regex.MULTILINE | regex.DOTALL
    ),
    'time': regex.compile(
        r'<div class="whenm">([0-9]+)\s(\w+)',
        regex.MULTILINE | regex.DOTALL
    ),
    'match_id': regex.compile(
        r'<a href="match\?m=([0-9]+)',
        regex.MULTILINE | regex.DOTALL
    ),
    'teams': regex.compile(
        r'<div class="team"(.*?)</i></div>',
        regex.MULTILINE | regex.DOTALL
    ),
    'team_name': regex.compile(
        r'<div class="teamtext"><b>(.*?)</b>',
        regex.MULTILINE | regex.DOTALL
    ),
    'won': regex.compile(
        r'(won.png)',
        regex.MULTILINE | regex.DOTALL
    ),
}


def main():
    html = requests.get(SITE_URL).text

    games = split_page(
        html,
        '<article class="standard" id="bets" style="margin-top: 40px;">',
        '</article>'
    )

    games_list = regex.findall(rgx['games'], games)

    for game in games_list:
        live = regex.search(rgx['live'], game)

        if not live:
            mongo_save(parse_game(game))


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

    time_regex = regex.findall(rgx['time'], game)
    time_list = list(time_regex[0])

    parsed_game['time'] = get_time(time_list[0], time_list[1])

    parsed_game['_id'] = regex.findall(rgx['match_id'], game)[0]

    team = regex.findall(rgx['teams'], game)

    parsed_game['team_1'] = regex.findall(rgx['team_name'], team[0])[0]

    parsed_game['team_2'] = regex.findall(rgx['team_name'], team[1])[0]

    parsed_game['won'] = 0

    if regex.findall(rgx['won'], team[0]):
        parsed_game['won'] = 1
    elif regex.findall(rgx['won'], team[1]):
        parsed_game['won'] = 2

    print(parsed_game)

    return parsed_game


def mongo_save(game):
    try:
        db.games.insert_one(game)
    except DuplicateKeyError:
        pass

if __name__ == '__main__':
    main()