from drf_spectacular.utils import extend_schema

from card_generator.api.v1.cards.serializers import CardSerializer, CardRenderSerializer
from card_generator.cards.models import Card
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


@extend_schema(tags=["cards"])
class CardViewSet(ModelViewSet):

    serializer_class = CardSerializer
    queryset = Card.objects.all()
    lookup_field = "uuid"
    authentication_classes = [TokenAuthentication]

    @action(
        methods=["post"],
        detail=True,
    )
    def render(self, request, **kwargs):
        """Apply values to card templates and render it in pdf and png formats."""
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
        """List all fields available for update."""
        data = {"fields": self.get_object().get_fields()}
        return Response(data=data)
