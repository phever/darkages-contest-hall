from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Contest, Entry, Vote

admin.site.register(User, UserAdmin)
admin.site.register(Contest)
admin.site.register(Entry)
admin.site.register(Vote)

