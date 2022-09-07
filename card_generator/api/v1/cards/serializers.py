import logging

from django.core.validators import FileExtensionValidator
from rest_framework import serializers
from rest_framework.fields import JSONField

from card_generator.cards.models import Card
from card_generator.cards.pdf import CardRender

log = logging.getLogger(__name__)


class CustomFileField(serializers.FileField):
    """Custom field for file that returns the url of the file."""

    def to_representation(self, value):
        return value.url


class CardSerializer(serializers.ModelSerializer):

    front_svg = CustomFileField(validators=[FileExtensionValidator(["svg"])])
    back_svg = CustomFileField(validators=[FileExtensionValidator(["svg"])])

    class Meta:
        model = Card
        exclude = ("created", "modified", "id")
        read_only_fields = ("uuid",)

        extra_kwargs = {"url": {"view_name": "api:cards", "lookup_field": "uuid"}}


class CardRenderSerializer(serializers.Serializer):
    """Serializer for rendering card template."""

    create_qr_code = serializers.BooleanField(default=True, write_only=True)
    __doc_create_qr_code__ = """Checks if the qrcode code should be generated with the value given.
    It checks for fields containing `qrcode`, gets the value provided and generate a QR code based on the value.
    """

    fields = JSONField(required=True, write_only=True)
    __doc_fields__ = """Dictionary of fields with its values."""

    files = serializers.SerializerMethodField()
    __doc_files__ = (
        """Files generated after applying the values on the card template."""
    )

    def get_files(self, obj):
        card = self.context["card"]
        card_render = CardRender(card, obj["fields"], obj["create_qr_code"])
        return card_render.render()

    def validate(self, data):
        create_qrcode = data["create_qr_code"]
        fields = data["fields"]
        items = [
            key
            for key, value in fields.items()
            if ("profile" in key or (not create_qrcode and "qrcode" in key))
            and "data:image" not in value
        ]

        if items:
            raise serializers.ValidationError(
                {
                    "fields": f"Fields `{', '.join(items)}` value should be in data uri format."
                }
            )
        return data
