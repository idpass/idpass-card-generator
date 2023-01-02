import base64

from django.conf import settings
from django.utils.functional import cached_property

SAMPLE_PDF = "card_generator/api/tests/v1/cards/samples/sample.pdf"


class OpenSPPClientTestMixin:
    @cached_property
    def sample_pdf(self):
        with open(SAMPLE_PDF, "rb") as file_read:
            encoded_string = base64.b64encode(file_read.read()).decode("utf-8")

        return encoded_string

    @cached_property
    def login_user_uid(self):
        return 1

    @cached_property
    def sample_queue_batch(self) -> dict:
        return {
            "id": 5,
            "name": "Batch 11-28-4",
            "queued_ids": [16, 17, 18, 19],
            "status": "generated",
            "id_pdf": self.sample_pdf,
            "id_pdf_filename": "None",
        }

    @cached_property
    def sample_id_queue(self) -> dict:
        return {
            "id": 16,
            "name": "None",
            "id_type": {"id": 6, "__str__": "PDS"},
            "idpass_id": {"id": 2, "__str__": "ePDS Card"},
            "registrant_id": {"id": 365, "__str__": "6411234634"},
            "id_pdf": self.sample_pdf,
            "id_pdf_filename": "PDS_6411234634_2022-11-28.pdf",
            "batch_id": {"id": 5, "__str__": "Batch 11-28-4"},
            "pds_number": "6411234634",
        }

    def server_proxy_execute_kw_side_effects(self, *args, **kwargs):
        if args[4] == "search_count":
            return 1
        elif args[4] in ["search_read", "write", "read"]:
            if args[3] == settings.OPENSPP_QUEUE_BATCH_MODEL:
                return [self.sample_queue_batch.copy()]
            return [self.sample_id_queue.copy()]
        elif args[4] == "fields_get":
            return {}
