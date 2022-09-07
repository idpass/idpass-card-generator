from django.contrib import admin

from card_generator.cards.models import Card


class CardModelAdmin(admin.ModelAdmin):
    list_display = ("title", "uuid")
    search_fields = ("title", "uuid")


admin.site.register(Card, CardModelAdmin)
