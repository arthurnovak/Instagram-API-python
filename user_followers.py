#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from InstagramAPI import InstagramAPI
from random import randrange
from random import shuffle
import time


login = ""
password = ""
max_likes_per_media = 3 #not more than 10
max_likes_per_day = 900
media_likes_limit = 500 #do not like a media if number of likes more than this value
user_name_list = []


def get_users_followers(user_id_next_max_list):
    followers = []
    new_user_id_next_max_list = []

    for user_next_max in user_id_next_max_list:
        user_id = user_next_max[0]
        next_max = user_next_max[1]
        (user_follower_list, new_next_max) = get_user_followers(user_id, next_max)
        followers += user_follower_list
        new_user_id_next_max_list += [(user_id, new_next_max)]

    return list(set(followers)), new_user_id_next_max_list


def get_user_followers(user_id, next_max_id):
    fllwrs = []
    new_next_max_id = ''

    api.getUserFollowers(user_id, next_max_id)
    result = api.LastJson
    for user in result['users']:
        fllwrs += [user['username']]
        new_next_max_id = result.get('next_max_id', '')

    return fllwrs, new_next_max_id


def get_media_ids(user_name):
    media_ids_and_count = []

    try:
        media_results = api.getUserRecentMedia(user_name)
        for media in media_results['items']:
            media_ids_and_count += [(media['id'], media['likes']['count'])]
    except Exception as e:
        write_log("User '%s' not found", user_name)

    return media_ids_and_count


def get_user_medias_and_like(user_name):
    media_ids_and_count = get_media_ids(user_name)

    if media_ids_and_count is []:
        write_log("No media to like found for username '%s'", user_name)
        return None
    else:
        top_medias = media_ids_and_count[:max_likes_per_media]
        for media in top_medias:
            if media[1] > media_likes_limit:
                write_log("Won't like media '%s' for username '%s' because already liked '%s' times", (media[0], user_name, media[1]))
                time.sleep(0.5)
            else:
                api.like(media[0])
                write_log("Liked media '%s' for username '%s'", (media[0], user_name))
                time.sleep(calc_sleep())
        return None


def get_user_ids(user_names):
    user_id_list = []

    for user_name in user_names:
        user_id = get_user_id(user_name)
        if user_id is not None:
            user_id_list += [user_id]
    return user_id_list


def get_user_id(user_name):
    try:
        media_results = api.getUserRecentMedia(user_name)
        result = media_results['items'][0]['user']['id']
    except Exception as e:
        write_log("User '%s' not found", user_name)
        result = None
    return result


def calc_sleep():
    sleep = 24 * 60 * 60 / max_likes_per_day
    return randrange(sleep - 5, sleep + 10)


def write_log(msg, args = None):
    now = time.strftime("%c")
    if args is None:
        print now, msg
    else:
        print now, msg % args

# Main
api = InstagramAPI(login, password)
api.login()

write_log("Get user ids for users: %s", user_name_list)
user_id_list = get_user_ids(user_name_list)
write_log("User ids are: %s", user_id_list)
user_id_next_max_list = [ (id, '') for id in user_id_list ]

while True:
    write_log("Get list of next followers for user ids")
    (follower_name_list, user_id_next_max_list) = get_users_followers(user_id_next_max_list)
    shuffle(follower_name_list)
    write_log("Followers list is: %s", follower_name_list)

    write_log("Start get media and like them")
    for name in follower_name_list:
        get_user_medias_and_like(name)
    # this block ^ should be repeated when list of followers is finished

api.logout()
