from django.urls import include, path

urlpatterns = [
    path("v1/", include("card_generator.api.v1.router")),
]
