#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from InstagramAPI import InstagramAPI
from random import randrange
from random import shuffle
import time
import json


class BotContext(object):
    def __init__(self, config_path):
        self.config_path            = config_path
        self.login                  = ''
        self.password               = ''
        self.max_likes_per_media    = 2 #not more than 10
        self.max_likes_per_day      = 900 #not more than 1000
        self.media_likes_limit      = 500 #do not like a media if number of likes more than this value
        self.user_name_list         = ['instagram']
        self.user_id_next_max_list  = []
        self.check_config_sec       = 300

        self.read_config()

    def __enter__(self):
        self.api = InstagramAPI(self.login, self.password)
        self.api.login()
        return self

    def __exit__(self, *args):
        write_log("Logging out")
        self.api.logout()

    def read_config(self):
        with open(self.config_path) as f:
            data = json.load(f)
            self.login                  = data.get('login', self.login)
            self.password               = data.get('password', self.password)
            self.max_likes_per_media    = data.get('max_likes_per_media', self.max_likes_per_media)
            self.max_likes_per_day      = data.get('max_likes_per_day', self.max_likes_per_day)
            self.media_likes_limit      = data.get('media_likes_limit', self.media_likes_limit)
            self.user_name_list         = data.get('user_name_list', self.user_name_list)
            self.user_id_next_max_list  = data.get('user_id_next_max_list', self.user_id_next_max_list)
            self.check_config_sec       = data.get('check_config_sec', self.check_config_sec)

    def write_config(self, update_dict):
        with open(self.config_path) as f:
            data = json.load(f)

        data.update(update_dict)

        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=4, sort_keys=True)


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


def get_media_ids(ctx, user_name):
    media_ids_and_count = []

    try:
        media_results = ctx.api.getUserRecentMedia(user_name)
        for media in media_results['items']:
            media_ids_and_count += [(media['id'], media['likes']['count'])]
    except Exception as e:
        write_log("User '%s' not found", user_name)

    return media_ids_and_count


def get_user_medias_and_like(ctx, user_name):
    media_ids_and_count = get_media_ids(ctx, user_name)

    if media_ids_and_count is []:
        write_log("No media to like found for username '%s'", user_name)
        return None
    else:
        top_medias = media_ids_and_count[:ctx.max_likes_per_media]
        for media in top_medias:
            if media[1] > ctx.media_likes_limit:
                write_log("Won't like media '%s' for username '%s' because already liked '%s' times", (media[0], user_name, media[1]))
                time.sleep(0.5)
            else:
                ctx.api.like(media[0])
                write_log("Liked media '%s' for username '%s'", (media[0], user_name))
                time.sleep(calc_sleep(ctx))
        return None


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
        write_log("User '%s' not found", user_name)
        result = None
    return result


def calc_sleep(ctx):
    sleep = 24 * 60 * 60 / ctx.max_likes_per_day
    return randrange(sleep - 5, sleep + 10)


def write_log(msg, args=None):
    now = time.strftime("%c")
    if args is None:
        print now, msg
    else:
        print now, msg % args


def write_user_id_next_max_list(ctx, user_id_next_max_list):
    ctx.write_config({'user_id_next_max_list': user_id_next_max_list})


def usort_users_with_next_max(user_id_list, user_id_next_max_list):
    newlist = []

    for id in user_id_list:
        is_found = False
        for id_next_max_pair in user_id_next_max_list:
            if id in id_next_max_pair:
                newlist += [id_next_max_pair]
                is_found = True
        if not is_found:
            newlist += [{id: ''}]

    return newlist


if __name__ == '__main__':
    with BotContext('config.json') as ctx:

        current_time = int(time.time())

        while True:
            write_log("Get user ids for users: %s", ctx.user_name_list)
            user_id_list = get_user_ids(ctx, ctx.user_name_list)
            write_log("User ids are: %s", user_id_list)

            user_id_next_max_list = usort_users_with_next_max(user_id_list, ctx.user_id_next_max_list)
            write_log("User ids and next max list: %s", user_id_next_max_list)

            write_log("Get list of next followers for user ids")
            (follower_name_list, user_id_next_max_list) = get_users_followers(ctx, user_id_next_max_list)

            write_user_id_next_max_list(ctx, user_id_next_max_list)

            shuffle(follower_name_list)
            write_log("Followers list is: %s", follower_name_list)

            write_log("Start get media and like them")
            for name in follower_name_list:
                # check config.json once per 'check_config_sec' interval
                if int(time.time()) - current_time > ctx.check_config_sec:
                    ctx.read_config()
                    current_time = int(time.time())

                get_user_medias_and_like(ctx, name)
        # this block ^ should be repeated when list of followers is finished
