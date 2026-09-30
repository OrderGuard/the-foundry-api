from django.contrib import admin
from .models import RewardConfig, UserPoints, SpinReward
from django import forms


class RewardConfigForm(forms.ModelForm):

    class Meta:
        model = RewardConfig
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        reward_type = self.data.get('reward_type') or getattr(self.instance, 'reward_type', None)

        if reward_type == 'discount':
            self.fields['free_item'].widget = forms.HiddenInput()

        elif reward_type == 'free_item':
            self.fields['value'].widget = forms.HiddenInput()
            self.fields['discount_type'].widget = forms.HiddenInput()

        elif reward_type == 'none':
            self.fields['value'].widget = forms.HiddenInput()
            self.fields['discount_type'].widget = forms.HiddenInput()
            self.fields['free_item'].widget = forms.HiddenInput()


@admin.register(RewardConfig)
class RewardConfigAdmin(admin.ModelAdmin):

    class Media:
        js = (
            "rewards/admin/reward_config.js",
        )

    form = RewardConfigForm

    list_display = ('name', 'reward_type','free_item', 'value', 'weight', 'is_active')
    list_editable = ('weight', 'is_active', 'value')
    list_filter = ('reward_type', 'is_active')
    search_fields = ('name',)


@admin.register(UserPoints)
class UserPointsAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'spins_available')


@admin.register(SpinReward)
class SpinRewardAdmin(admin.ModelAdmin):
    list_display = ('user', 'reward_config', 'coupon', 'status',  'expires_at', 'created_at')
    list_filter = ('reward_config', 'created_at')
    search_fields = ('user__username', 'coupon')
