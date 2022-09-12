import uuid
from collections import OrderedDict

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from card_generator.cards.utils import get_svg_fields_from_tags, get_svg_variables


class Card(TimeStampedModel):

    title = models.CharField(_("Title"), max_length=50)
    front_svg = models.FileField(
        upload_to="cards/", validators=[FileExtensionValidator(["svg"])]
    )
    back_svg = models.FileField(
        upload_to="cards/", validators=[FileExtensionValidator(["svg"])]
    )
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True)

    def __str__(self):
        return self.title

    def get_fields(self) -> list:
        """Get available fields the user can update."""
        # This gets the fields tagged in `data-variable`
        front_svg_fields = get_svg_fields_from_tags(self.front_svg.path)
        back_svg_fields = get_svg_fields_from_tags(self.back_svg.path)

        # This gets the fields declared in `{{ }}`
        front_svg_fields.extend(get_svg_variables(self.front_svg.path))
        back_svg_fields.extend(get_svg_variables(self.back_svg.path))
        fields = front_svg_fields + back_svg_fields

        unique_fields = list(
            OrderedDict((frozenset(item.items()), item) for item in fields).values()
        )

        return unique_fields
