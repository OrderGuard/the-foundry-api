import random

def get_weighted_reward(rewards):
    weighted_list = []

    for r in rewards:
        weighted_list.extend([r] * r.weight)

    return random.choice(weighted_list)
