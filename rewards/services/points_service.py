# apps/rewards/services/points_service.py

from rewards.models import UserPoints

THRESHOLD = 50  # 50 points = 1 spin


def add_points(user, amount):
    obj, _ = UserPoints.objects.get_or_create(user=user)

    obj.points += amount

    # convert to spins
    while obj.points >= THRESHOLD:
        obj.points -= THRESHOLD
        obj.spins_available += 1

    obj.save()

    return obj

