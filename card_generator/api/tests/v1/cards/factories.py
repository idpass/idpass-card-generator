import factory
from faker import Faker

from card_generator.cards.models import Card

fake = Faker()


class CardFactory(factory.django.DjangoModelFactory):

    title = fake.text(20)
    front_svg = fake.file_name(category="image", extension="svg")
    back_svg = fake.file_name(category="image", extension="svg")

    class Meta:
        model = Card
