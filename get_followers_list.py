#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from InstagramAPI import InstagramAPI
from random import randrange
import time


class BotContext(object):
    def __init__(self):
        self.login                     = 'arthurinside'
        self.password                  = 'wsdetupInsta21'
        self.followers_list_size_limit = 10000
        self.user_name_list            = ["abramov_lex", "kylekrieger", "nusrulla_s"]

    def __enter__(self):
        self.api = InstagramAPI(self.login, self.password)
        self.api.login()
        # time.sleep(5)
        # self.api.login2()
        return self

    def __exit__(self, *args):
        self.api.logout()
        # time.sleep(3)
        # self.api.logout2()
        log(self, "Logged out")


def get_users_followers(ctx, user_id_next_max_list):
    followers = []
    new_user_id_next_max_list = []

    for user_next_max in user_id_next_max_list:
        user_id = user_next_max.keys()[0]
        next_max = user_next_max[user_id]
        (user_follower_list, new_next_max) = get_user_followers(ctx, user_id, next_max)
        followers += user_follower_list
        new_user_id_next_max_list += [{user_id: new_next_max}]

    return list(set(followers)), new_user_id_next_max_list


def get_user_followers(ctx, user_id, next_max_id):
    fllwrs = []
    new_next_max_id = ''

    ctx.api.getUserFollowers(user_id, next_max_id)
    result = ctx.api.LastJson
    for user in result['users']:
        fllwrs += [user['username']]
        new_next_max_id = result.get('next_max_id', '')

    return fllwrs, new_next_max_id


def get_user_ids(ctx, user_names):
    user_id_list = []

    for user_name in user_names:
        user_id = get_user_id(ctx, user_name)
        if user_id is not None:
            user_id_list += [user_id]
    return user_id_list


def get_user_id(ctx, user_name):
    try:
        media_results = ctx.api.getUserRecentMedia(user_name)
        result = media_results['items'][0]['user']['id']
    except Exception as e:
        log(ctx, "User '%s' not found", user_name)
        result = None
    return result


def calc_sleep(ctx):
    sleep = day_secs / ctx.max_likes_per_day
    half_sleep = sleep / 2
    return randrange(sleep - half_sleep, sleep + half_sleep)


def log(ctx, msg, args=None):
    if args is None:
        ctx.api.log(msg)
    else:
        ctx.api.log(msg % args)


if __name__ == '__main__':
    with BotContext() as ctx:

        final_follower_name_list = []

        log(ctx, "Get user ids for users: %s", ctx.user_name_list)
        user_id_list = get_user_ids(ctx, ctx.user_name_list)
        log(ctx, "User ids are: %s", user_id_list)

        user_id_next_max_list = [ {user_id: ''} for user_id in user_id_list ]

        while len(final_follower_name_list) < ctx.followers_list_size_limit:
            log(ctx, "List of followers size: %s. Get list of next followers for user ids", len(final_follower_name_list))
            (follower_name_list, user_id_next_max_list) = get_users_followers(ctx, user_id_next_max_list)

            final_follower_name_list += follower_name_list
            time.sleep(2)

        log(ctx, "Final followers list: %s", final_follower_name_list)
        log(ctx, "Final user_id next_max list: %s", user_id_next_max_list)

# Final user_id next_max list: [{u'1861652': u'AQABqgLPyd9Y4gm0G8r6zbVpucuDBJLxw4zkfl9CjVvpdi9cKk_oVcZ0Rlo18uU6XPCpuwWy4IybJUq6LRmKRVmQMMetCyC-N8JLXYGzQWCjHw'}, {u'15185639': u'AQC36fZDw9RlfiTunfWMcP1cn_LVnoo5X1WWljm9I2GkkRAOItxZ8XB2pcrRUmFshnNV9aQGUcfha5mPkiRFVyU5UxQGUVDNXNdqPv7KTT0Dig'}, {u'302150087': u'AQDJZN8TMEnygg760wqN9T3pPKzqD76iGSuqouVUNBYWlLHN5sLdHhOFJqEjL2FZFsUFrFoqvLyHdGkkOXHw8-SA166Se-eLXBEIepHnL4MQaw'}]
