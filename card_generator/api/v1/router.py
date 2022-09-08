from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from card_generator.api.v1.cards.views import CardViewSet
from card_generator.api.v1.users.views import UserViewSet
from card_generator.lib.api.routers import DefaultRouter

router = DefaultRouter()
router.register("users", UserViewSet)
router.register("cards", CardViewSet)
router.add_path(path("auth-token/", obtain_auth_token))

app_name = "api-v1"
urlpatterns = router.urls
