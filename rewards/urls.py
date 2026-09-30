# apps/rewards/urls.py

from django.urls import path
# from .views import spin_wheel, reward_history, reward_status
from .views import (
    spin_wheel,
    reward_status,
    wheel_config,
    reward_history,
    redeem_reward,
    unredeem_reward
)

urlpatterns = [
    path('spin/', spin_wheel, name='spin-wheel'),
    path('wheel/', wheel_config, name='wheel-config'),

    # 📜 show past rewards
    # path('history/', reward_history, name='reward-history'),

    # show points + spins
    path('status/', reward_status, name='reward-status'),
    path('history/', reward_history, name='reward-history'),
    # redeem
    path(
        "redeem/<int:reward_id>/",
        redeem_reward,
        name="redeem_reward",
    ),
    path(
        "unredeem/<int:reward_id>/",
        unredeem_reward,
    ),

]

