from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from card_generator.api.v1.cards.serializers import CardRenderSerializer, CardSerializer
from card_generator.cards.models import Card


@extend_schema(tags=["cards"])
@extend_schema_view(
    list=extend_schema(description="List all available card templates."),
    retrieve=extend_schema(description="Retrieve a card template."),
    create=extend_schema(description="Create a new card template."),
    update=extend_schema(description="Update a card template."),
    delete=extend_schema(description="Remove a card template."),
)
class CardViewSet(ModelViewSet):

    serializer_class = CardSerializer
    queryset = Card.objects.all()
    lookup_field = "uuid"
    authentication_classes = (TokenAuthentication,)
    http_method_names = ("get", "post", "put", "delete")

    @action(
        methods=["post"],
        detail=True,
    )
    def render(self, request, **kwargs):
        """Generate a card from a template with the provided values."""
        serializer = CardRenderSerializer(
            data=request.data, context={"card": self.get_object()}
        )
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.data)

    @action(
        methods=["get"],
        detail=True,
    )
    def fields(self, request, **kwargs):
        """List all variable fields present in the template where the user can provide a value."""
        data = {"fields": self.get_object().get_fields()}
        return Response(data=data)
