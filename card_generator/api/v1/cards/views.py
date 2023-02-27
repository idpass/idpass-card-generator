import logging

from django.conf import settings
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from card_generator.api.v1.cards.serializers import CardRenderSerializer, CardSerializer
from card_generator.cards.client import QueueCardsClient
from card_generator.cards.models import Card
from card_generator.tasks.cards import merge_cards as merge_cards_task

logger = logging.getLogger(__name__)


@extend_schema(tags=["cards"])
@extend_schema_view(
    list=extend_schema(description="List all available card templates."),
    retrieve=extend_schema(description="Retrieve a card template."),
    create=extend_schema(description="Create a new card template."),
    update=extend_schema(description="Update a card template."),
    delete=extend_schema(description="Remove a card template."),
)
class CardViewSet(ModelViewSet):
    """
    ViewSet for all card related actions.
    """

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
        """
        Generate a card from a template with the provided values.
        :param request: Request object
        :param kwargs: Unrequired keyword arguments that may be passed to this function
        :return: Response object with the data rendered.
        """
        front_only = self.request.query_params.get("front_only")
        serializer = CardRenderSerializer(
            data=request.data,
            context={"card": self.get_object(), "front_only": front_only},
        )
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.data)

    @action(
        methods=["get"],
        detail=True,
    )
    def fields(self, request, **kwargs):
        """
        List all variable fields present in the template where the user can provide a value.
        :param request: Request object
        :param kwargs: Unrequired keyword arguments that may be passed to this function
        :return: Response object with the list of fields
        """
        data = {"fields": self.get_object().get_fields()}
        return Response(data=data)

    @extend_schema(
        examples=[OpenApiExample(value={"batch_id": 1}, name="Sample request")],
    )
    @action(methods=["post"], detail=True, url_path="openspp/merge-cards")
    def merge_cards(self, request, **kwargs):
        """
        This is a dedicated action for OpenSPP. It accepts a batch queue ID and will return a message. The actual
        process of merging cards is done through a background process.
        :param request: Request object
        :param kwargs: Unrequired keyword arguments that may be passed to this function
        :return: Response object with a message
        """
        batch_id = request.data.get("batch_id")
        if not batch_id:
            return Response(status=400, data={"message": "Missing 'batch_id'."})
        if not isinstance(batch_id, str) and not isinstance(batch_id, int):
            return Response(status=400, data={"message": "Invalid 'batch_id'."})

        if isinstance(batch_id, str) and not batch_id.isnumeric():
            return Response(status=400, data={"message": "Invalid 'batch_id'."})

        client = QueueCardsClient(
            server_root=settings.OPENSPP_SERVER_ROOT,
            username=settings.OPENSPP_USERNAME,
            password=settings.OPENSPP_API_TOKEN,
            db_name=settings.OPENSPP_DB_NAME,
        )
        record = client.get_queue_batch(batch_id=batch_id)
        if not record:
            return Response(
                status=404,
                data={"message": f"No data associated with Batch ID {batch_id}"},
            )
        logger.info(f"Batch ID #{batch_id}")
        merge_cards_task.delay(batch_id=int(batch_id))

        return Response(
            status=200,
            data={
                "message": "We are merging the cards. This process will automatically "
                "update the batch record with the merged card pdf."
            },
        )
