import os
from typing import Set

import pickle
import numpy as np

from termcolor import cprint

from network import UserNetwork, NETWORK_PATH

SIZE_LIMIT = 10000 * 10000
USER_SET_PATH = os.path.join(NETWORK_PATH, "user_set")


def dump_user_set(user_set, file):
    with open(os.path.join(USER_SET_PATH, file), 'wb') as f:
        pickle.dump(user_set, f)
    cprint("Dump user set: {} in {} users".format(file, len(user_set)), "blue")


def load_user_set(file):
    with open(os.path.join(USER_SET_PATH, file), 'rb') as f:
        loaded_user_set = pickle.load(f)
        cprint("Load user set: {} in {} users".format(file, len(loaded_user_set)), "green")
        return loaded_user_set


def dump_user_set_distributively(user_set, file_prefix, number=3):
    base = 0
    size = int(len(user_set)/number) + 1
    user_list = list(user_set)
    for i in range(number):
        sub_user_set = set(user_list[base:base+size])
        dump_user_set(sub_user_set, f"{file_prefix}_{i}.pkl")
        base += size


def load_user_set_distributively(file_prefix):
    user_list = []
    for i, file in enumerate([f for f in os.listdir(USER_SET_PATH) if f.startswith(file_prefix)]):
        sub_user_set = load_user_set(file)
        user_list += list(sub_user_set)
    return set(user_list)


def get_unique_user_partition_set_from_network(file_name: str, what_to_crawl: str):
    user_network = UserNetwork()
    user_network.load(file_name=file_name)

    user_set: Set[int] = set()

    if file_name:
        user_id_to_x = user_network.user_id_to_friend_ids
    else:
        user_id_to_x = user_network.user_id_to_follower_ids

    total_length = 0

    i = -1
    for i, (user, f_list) in enumerate(user_id_to_x.items()):

        if f_list is None:
            user_set.add(int(user))
            continue

        length = len(user_set)

        if length + len(f_list) >= SIZE_LIMIT:
            dump_user_set(user_set, "user_set_{}_{}.pkl".format(what_to_crawl, i))
            user_set = set()

        user_set.add(int(user))
        user_set.update(f_list)
        total_length += length + 1

    else:
        if len(user_set) != 0:
            dump_user_set(user_set, "user_set_{}_{}.pkl".format(what_to_crawl, i))

    print("Total length: {}".format(total_length))


def reduce_user_partition(what_to_crawl, new_limit):

    file_list = sorted([f for f in os.listdir(USER_SET_PATH)
                        if what_to_crawl in f and f.startswith("user_set")])

    total_user_set = set()
    i = -1
    for i, file_name in enumerate(file_list):
        user_set = load_user_set(file_name)
        total_user_set.update(user_set)
        print("Current total_user_set: {}".format(len(total_user_set)))

        if len(total_user_set) >= new_limit:
            dump_user_set(total_user_set, "reduced_user_set_{}_{}.pkl".format(what_to_crawl, i))
            total_user_set = set()

    else:
        if len(total_user_set) != 0:
            dump_user_set(total_user_set, "reduced_user_set_{}_{}.pkl".format(what_to_crawl, i))


def reduce_to_one_and_dump_distributively(what_to_crawl, file_prefix,
                                          file_prefix_to_merge="reduced_user_set", number=2):
    file_list = sorted([f for f in os.listdir(USER_SET_PATH)
                        if what_to_crawl in f and f.startswith(file_prefix_to_merge)])

    total_user_set = set()
    for i, file_name in enumerate(file_list):
        user_set = load_user_set(file_name)
        total_user_set.update(user_set)

    dump_user_set_distributively(total_user_set, file_prefix, number)


def get_tiny_user_set(base_file_name, tiny_size):
    user_set = load_user_set(base_file_name)
    tiny_user_set = set(list(user_set)[:tiny_size])
    dump_user_set(tiny_user_set, "tiny_{}".format(base_file_name))


def get_user_set_minus_propagated_user_set():

    user_set = load_user_set_distributively("one_user_set")

    user_network = UserNetwork()
    user_network.load("UserNetwork_friends.pkl")
    propagated_user_set = set(int(u) for u in user_network.user_id_to_friend_ids)

    dump_user_set_distributively(user_set-propagated_user_set, "not_propagated_user_set_follower", 2)


def sample_user_set(original_file, sample_num):
    user_ndarray = np.asarray(list(load_user_set_distributively(original_file)))
    permutation = np.random.permutation(user_ndarray.size)
    indices = permutation[:sample_num]
    sampled = set(user_ndarray[indices])
    dump_user_set_distributively(sampled, "sampled_{}".format(original_file), 1)
    return sampled


if __name__ == '__main__':

    MODE = "SAMPLE_USER_SET"

    what_to_crawl_in_main = "follower"
    main_file_name = "UserNetwork_friends.pkl" if what_to_crawl_in_main == "friend" else None

    if MODE == "GET_PARTITION":
        get_unique_user_partition_set_from_network(main_file_name, what_to_crawl_in_main)

    elif MODE == "REDUCE_PARTITION":
        reduce_user_partition(what_to_crawl_in_main, 250000000)

    elif MODE == "REDUCE_PARTITION_DIST":
        reduce_to_one_and_dump_distributively(
            what_to_crawl_in_main,
            "one_user_set_{}".format(what_to_crawl_in_main),
            "one_user_set"
        )

    elif MODE == "GET_TINY_USER_SET":
        get_tiny_user_set("one_user_set_follower_0 (201270329).pkl", 1000)

    elif MODE == "MINUS_PROPAGATED":
        get_user_set_minus_propagated_user_set()

    elif MODE == "SAMPLE_USER_SET":
        sample_user_set("not_propagated_user_set_follower", int(79416/4))
