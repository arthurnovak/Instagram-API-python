#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from InstagramAPI import InstagramAPI
from random import randrange
from random import shuffle
import time
import json


day_secs = 86400
ban_err_idle_sec = 60 * 60
other_err_idle_sec = 30


class BotContext(object):
    def __init__(self, config_path):
        self.config_path            = config_path
        self.login                  = ''
        self.password               = ''
        self.max_likes_per_media    = 2 #not more than 10
        self.max_likes_per_day      = 900 #not more than 1000
        self.media_likes_limit      = 500 #do not like a media if number of likes more than this value
        self.user_name_list         = ['instagram']
        self.last_username         = ''
        self.check_config_sec       = 300
        self.day_likes_acc          = 0

        self.read_config()

        # sys.stdout = open('output.log', 'w')

    def __enter__(self):
        self.api = InstagramAPI(self.login, self.password)
        # self.api.login()
        # time.sleep(5)
        self.api.login2()
        return self

    def __exit__(self, *args):
        # self.api.logout()
        # time.sleep(3)
        self.api.logout2()
        log(self, "Logged out\n")

    def read_config(self):
        with open(self.config_path) as f:
            data = json.load(f)
            self.login                  = data.get('login', self.login)
            self.password               = data.get('password', self.password)
            self.max_likes_per_media    = data.get('max_likes_per_media', self.max_likes_per_media)
            self.max_likes_per_day      = data.get('max_likes_per_day', self.max_likes_per_day)
            self.media_likes_limit      = data.get('media_likes_limit', self.media_likes_limit)
            self.user_name_list         = data.get('user_name_list', self.user_name_list)
            self.last_username          = data.get('last_username', self.last_username)
            self.check_config_sec       = data.get('check_config_sec', self.check_config_sec)

    def write_config(self, update_dict):
        with open(self.config_path) as f:
            data = json.load(f)

        data.update(update_dict)

        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=4, sort_keys=True)


def get_media_ids(ctx, user_name):
    media_ids_and_count = []

    try:
        media_results = ctx.api.getUserRecentMediaWoApi(user_name)
        for media in media_results['items']:
            media_ids_and_count += [(media['id'], media['likes']['count'])]
    except Exception as e:
        log(ctx, "User '%s' not found", user_name)

    return media_ids_and_count


def get_user_medias_and_like(ctx, user_name):
    media_ids_and_count = get_media_ids(ctx, user_name)
    write_last_username(ctx, user_name)

    if media_ids_and_count is []:
        log(ctx, "No media to like found for username '%s'", user_name)
        return None
    else:
        top_medias = media_ids_and_count[:ctx.max_likes_per_media]
        for media in top_medias:
            if media[1] > ctx.media_likes_limit:
                log(ctx, "Won't like media '%s' for username '%s' because already liked '%s' times", (media[0], user_name, media[1]))
                time.sleep(0.5)
            else:
                resp = ctx.api.likeMediaWoApi(media[0])
                status_code = resp.status_code
                if status_code == 200:
                    new_day_likes_acc = ctx.day_likes_acc + 1
                    ctx.day_likes_acc = new_day_likes_acc
                    log(ctx, "Liked media '%s' for username '%s'", (media[0], user_name))
                    time.sleep(calc_sleep(ctx))
                elif status_code == 400:
                    #oops, may be banned
                    log(ctx,
                        "Error response code %s returned when like username '%s' media. Try again in %s seconds...",
                        (status_code, user_name, ban_err_idle_sec))
                    time.sleep(ban_err_idle_sec)
                else:
                    log(ctx,
                        "Error response code %s returned when like username '%s' media. Sleep for %s seconds now...",
                        (resp.status_code, user_name, other_err_idle_sec))
                    time.sleep(other_err_idle_sec)
        return None


def calc_sleep(ctx):
    sleep = day_secs / ctx.max_likes_per_day
    half_sleep = sleep / 2
    return randrange(sleep - half_sleep, sleep + half_sleep)


def log(ctx, msg, args=None):
    if args is None:
        ctx.api.log(msg)
    else:
        ctx.api.log(msg % args)


def write_last_username(ctx, username):
    ctx.write_config({'last_username': username})


if __name__ == '__main__':
    with BotContext('config.json') as ctx:

        current_time = int(time.time())
        day_start_time = current_time
        new_user_name_list = []

        if ctx.last_username:
            log(ctx, "here")
            # split list by last_username. Take second part
            user_name_list = ctx.user_name_list
            index = user_name_list.index(ctx.last_username)
            new_user_name_list = [user_name_list[:index], user_name_list[index+1:]][1]
            log(ctx, "Users to like list: %s", new_user_name_list)
        else:
            new_user_name_list = ctx.user_name_list

        log(ctx, "Start get media and like them")
        for name in new_user_name_list:
            new_current_time = int(time.time())

            # check config.json once per 'check_config_sec' interval
            if new_current_time - current_time > ctx.check_config_sec:
                ctx.read_config()
                current_time = new_current_time

            # check every 24h that likes limit for day is not exceeded
            seconds_since_day_starts = new_current_time - day_start_time
            if seconds_since_day_starts > day_secs:
                day_start_time = new_current_time
                log(ctx, "One day passed. 'day_likes_acc' is %s. Reset to 0 now", ctx.day_likes_acc)
                ctx.day_likes_acc = 0
            else:
                if ctx.day_likes_acc > ctx.max_likes_per_day - ctx.max_likes_per_media:
                    log(ctx,
                        "Day hasn't finished yet, but we liked %s posts. Will sleep for %s seconds until new day...",
                        (ctx.day_likes_acc, day_secs - seconds_since_day_starts))
                    time.sleep(day_secs - seconds_since_day_starts)

            get_user_medias_and_like(ctx, name)

        log(ctx, "Username list is finished. Job done")
