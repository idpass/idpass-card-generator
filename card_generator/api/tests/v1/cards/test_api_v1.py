import base64

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from card_generator.api.tests.v1.cards.factories import CardFactory
from card_generator.cards.exceptions import QRCodeCharLimitException
from card_generator.users.tests.factories import UserFactory

CARD_TITLE_1 = "Sample Title"
FRONT_SVG_FILE = "card_generator/api/tests/v1/cards/samples/front_card.svg"
BACK_SVG_FILE = "card_generator/api/tests/v1/cards/samples/back_card.svg"
JPG_FILE = "card_generator/api/tests/v1/cards/samples/sample_image.jpg"


class CardTestCase(APITestCase):
    """
    Test for /api/cards/ endpoint
    Accepts POST (create) and GET (list)
    """

    def setUp(self) -> None:
        self.url = reverse("api-v1:card-list")
        self.card_1 = CardFactory()
        self.card_2 = CardFactory()

        user = UserFactory()
        self.client.force_authenticate(user)

    def test_cards_list(self):
        response = self.client.get(self.url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(self.card_1.title, response.data[0]["title"])
        self.assertEqual(self.card_1.uuid.__str__(), response.data[0]["uuid"])
        self.assertEqual(self.card_2.title, response.data[1]["title"])
        self.assertEqual(self.card_2.uuid.__str__(), response.data[1]["uuid"])

    def test_create_valid_card(self):
        with open(FRONT_SVG_FILE, "rb") as front_svg, open(
            BACK_SVG_FILE, "rb"
        ) as back_svg:
            data = {
                "title": CARD_TITLE_1,
                "front_svg": front_svg,
                "back_svg": back_svg,
            }

            response = self.client.post(self.url, data=data, format="multipart")

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(CARD_TITLE_1, response.data["title"])
        self.assertTrue(response.data["uuid"])

    def test_create_with_string(self):
        data = {"title": CARD_TITLE_1, "front_svg": "random", "back_svg": "random"}

        response = self.client.post(self.url, data=data, format="multipart")
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(
            "The submitted data was not a file. Check the encoding type on the form.",
            response.data["front_svg"][0].__str__(),
        )
        self.assertEqual(
            "The submitted data was not a file. Check the encoding type on the form.",
            response.data["back_svg"][0].__str__(),
        )

    def test_create_image_file_format(self):
        data = {
            "title": CARD_TITLE_1,
            "front_svg": open(JPG_FILE, "rb"),
            "back_svg": open(JPG_FILE, "rb"),
        }

        response = self.client.post(self.url, data=data, format="multipart")
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(
            "File extension “jpg” is not allowed. Allowed extensions are: svg.",
            response.data["front_svg"][0].__str__(),
        )
        self.assertEqual(
            "File extension “jpg” is not allowed. Allowed extensions are: svg.",
            response.data["back_svg"][0].__str__(),
        )

    def test_anonymous_user_get_cards_list(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual(
            "Authentication credentials were not provided.", response.json()["detail"]
        )

    def test_anonymous_user_create_card(self):
        self.client.logout()
        with open(FRONT_SVG_FILE, "rb") as front_svg, open(
            BACK_SVG_FILE, "rb"
        ) as back_svg:
            data = {
                "title": CARD_TITLE_1,
                "front_svg": front_svg,
                "back_svg": back_svg,
            }
            response = self.client.post(self.url, data=data, format="multipart")
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual(
            "Authentication credentials were not provided.", response.json()["detail"]
        )


class CardDetailTestCase(APITestCase):
    """
    Test for /cards/<uuid:uuid>/ endpoints
    Accepts POST (render pdf) and GET (retrieve)
    """

    def setUp(self) -> None:
        user = UserFactory()
        self.client.force_authenticate(user)
        with open(FRONT_SVG_FILE, "rb") as front_svg_file, open(
            BACK_SVG_FILE, "rb"
        ) as back_svg_file:
            data = {
                "title": CARD_TITLE_1,
                "front_svg": front_svg_file,
                "back_svg": back_svg_file,
            }

            response = self.client.post("/api/v1/cards/", data=data, format="multipart")
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self.detail_url = reverse(
            "api-v1:card-detail", kwargs={"uuid": response.data["uuid"]}
        )
        self.render_url = reverse(
            "api-v1:card-render", kwargs={"uuid": response.data["uuid"]}
        )
        self.fields_url = reverse(
            "api-v1:card-fields", kwargs={"uuid": response.data["uuid"]}
        )

    def test_detail(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(CARD_TITLE_1, response.data["title"])

    def test_get_wrong_uuid(self):
        url = "/api/v1/cards/random-601b-4905-b0ff-edfb7c6ffa48/"

        response = self.client.get(url)
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_card_render(self):
        with open(FRONT_SVG_FILE, "rb") as svg_file:
            sample_image_b64 = base64.b64encode(svg_file.read()).decode("utf-8")
        sample_image = f"data:image/svg+xml;base64,{sample_image_b64}"
        data = {
            "create_qr_code": True,
            "fields": {
                "given_name": "Test User",
                "identification_no": "idnum123",
                "profile_svg_3": sample_image,
                "sex": "M",
                "date_of_birth": "Jan 1, 1990",
                "date_of_expiry": "Jan 30, 2025",
                "date_of_issue": "Jan 1, 2020",
                "nationality": "Sample",
                "surname": "Doe",
                "qrcode_svg_15": "123182390178293712",
            },
        }

        response = self.client.post(self.render_url, data, format="json")
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertTrue(response.data["files"]["pdf"])
        self.assertTrue(response.data["files"]["png"])

    def test_anonymous_user_render_card(self):
        self.client.logout()
        with open(FRONT_SVG_FILE, "rb") as svg_file:
            sample_image_b64 = base64.b64encode(svg_file.read()).decode("utf-8")
        sample_image = f"data:image/svg+xml;base64,{sample_image_b64}"
        data = {
            "create_qr_code": True,
            "fields": {
                "given_name": "Test User",
                "identification_no": "idnum123",
                "profile_svg_3": sample_image,
                "sex": "M",
                "date_of_birth": "Jan 1, 1990",
                "date_of_expiry": "Jan 30, 2025",
                "date_of_issue": "Jan 1, 2020",
                "nationality": "Sample",
                "surname": "Doe",
                "qrcode_svg_15": "123182390178293712",
            },
        }

        response = self.client.post(self.render_url, data, format="json")
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual(
            "Authentication credentials were not provided.", response.json()["detail"]
        )

    def test_card_render_provide_qr_code(self):
        with open(FRONT_SVG_FILE, "rb") as svg_file:
            sample_image_b64 = base64.b64encode(svg_file.read()).decode("utf-8")
        sample_image = f"data:image/svg+xml;base64,{sample_image_b64}"
        data = {
            "create_qr_code": False,
            "fields": {
                "given_name": "Test User",
                "identification_no": "idnum123",
                "profile_svg_3": sample_image,
                "sex": "M",
                "date_of_birth": "Jan 1, 1990",
                "date_of_expiry": "Jan 30, 2025",
                "date_of_issue": "Jan 1, 2020",
                "nationality": "Sample",
                "surname": "Doe",
                "qrcode_svg_15": sample_image,
            },
        }

        response = self.client.post(self.render_url, data, format="json")
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertTrue(response.data["files"]["pdf"])
        self.assertTrue(response.data["files"]["png"])

    def test_card_render_provided_qr_code_wrong_format(self):
        with open(FRONT_SVG_FILE, "rb") as svg_file:
            sample_image_b64 = base64.b64encode(svg_file.read()).decode("utf-8")
        sample_image = f"data:image/svg+xml;base64,{sample_image_b64}"
        data = {
            "create_qr_code": False,
            "fields": {
                "given_name": "Test User",
                "identification_no": "idnum123",
                "profile_svg_3": sample_image,
                "sex": "M",
                "date_of_birth": "Jan 1, 1990",
                "date_of_expiry": "Jan 30, 2025",
                "date_of_issue": "Jan 1, 2020",
                "nationality": "Sample",
                "surname": "Doe",
                "qrcode_svg_15": sample_image_b64,
            },
        }

        response = self.client.post(self.render_url, data, format="json")
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(
            "Fields `qrcode_svg_15` value should be in data uri format.",
            response.data["fields"][0].__str__(),
        )

    def test_card_render_nonexistent_fields(self):
        data = {
            "fields": {
                "given_name": "Test User",
                "random": "00000000001",
                "identification_no": "10000100000",
            }
        }

        response = self.client.post(self.render_url, data, format="json")
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_card_fields(self):
        fields = [
            {"tag": "image", "name": "profile_svg_3"},
            {"tag": "text", "name": "sex"},
            {"tag": "text", "name": "date_of_birth"},
            {"tag": "text", "name": "date_of_expiry"},
            {"tag": "text", "name": "identification_no"},
            {"tag": "text", "name": "date_of_issue"},
            {"tag": "text", "name": "given_name"},
            {"tag": "text", "name": "nationality"},
            {"tag": "text", "name": "surname"},
            {"tag": "image", "name": "qrcode_svg_15"},
        ]
        response = self.client.get(self.fields_url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(10, len(response.data["fields"]))
        for field in fields:
            self.assertIn(field, response.data["fields"])

    def test_anonymous_user_card_fields(self):
        self.client.logout()
        response = self.client.get(self.fields_url)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual(
            "Authentication credentials were not provided.", response.json()["detail"]
        )

    def test_card_render_create_qrcode_with_data_uri(self):
        """
        Test creating qrcode with input using data uri.
        We will allow it because we prioritize checking `create_qr_code` field.
        """
        with open(FRONT_SVG_FILE, "rb") as svg_file:
            sample_image_b64 = base64.b64encode(svg_file.read()).decode("utf-8")
        sample_image = f"data:image/svg+xml;base64,{sample_image_b64}"
        data = {
            "create_qr_code": True,
            "fields": {
                "given_name": "Test User",
                "identification_no": "idnum123",
                "profile_svg_3": sample_image,
                "sex": "M",
                "date_of_birth": "Jan 1, 1990",
                "date_of_expiry": "Jan 30, 2025",
                "date_of_issue": "Jan 1, 2020",
                "nationality": "Sample",
                "surname": "Doe",
                "qrcode_svg_15": sample_image,
            },
        }

        with self.assertRaises(QRCodeCharLimitException):
            self.client.post(self.render_url, data, format="json")
