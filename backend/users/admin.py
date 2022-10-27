from django.contrib import admin

from users.models import Follow, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Класс админ-панели, отвечающий за пользователей."""

    list_display = (
        'pk',
        'username',
        'email',
        'first_name',
        'last_name',
    )
    search_fields = ('username', 'email',)
    list_filter = ('username', 'email',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Класс админ-панели, отвечающий за подписки."""

    list_display = ('pk', 'user', 'following',)
    search_fields = ('user', 'following',)
    list_filter = ('user', 'following',)


admin.sites.AdminSite.empty_value_display = '-пусто-'
