#!/usr/bin/env python

from datetime import datetime, timedelta

from lxml import html
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

import requests

SITE_URL = 'http://dota2lounge.com/'

client = MongoClient('mongodb://localhost:27017/')
db = client.d2l_xml


def main():
    page = requests.get(SITE_URL)

    tree = html.document_fromstring(page.text)

    games = tree.xpath('//div[@class="matchmain"]')

    for game in games:
        time_holder = game.xpath('.//div[@class="whenm"]').pop()

        future = 'from now' in time_holder.text

        is_live = len(time_holder.xpath('.//span')) == 2

        if not future and not is_live:
            mongo_save(parse_game(game, time_holder))

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


def parse_game(game, time_holder):
    parsed_game = {}

    parsed_game['time'] = get_time(*time_holder.text.split(' ')[:2])

    parsed_game['_id'] = int(game.xpath('.//a').pop().attrib['href'].split('=')[1])

    teams = game.xpath('.//div[@class="teamtext"]/b')

    parsed_game['team_1'] = teams[0].text

    parsed_game['team_2'] = teams[1].text

    teams = game.xpath('.//div[@class="team"]')

    # import ipdb
    # ipdb.set_trace()

    if teams[0].xpath('.//img'):
        parsed_game['won'] = 1
    elif teams[1].xpath('.//img'):
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
