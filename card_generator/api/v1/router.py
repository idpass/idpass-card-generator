from card_generator.api.v1.users.views import UserViewSet
from card_generator.lib.api.routers import DefaultRouter

router = DefaultRouter()
router.register("users", UserViewSet)


app_name = "api-v1"
urlpatterns = router.urls
