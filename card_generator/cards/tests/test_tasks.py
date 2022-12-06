from unittest import mock

from django.conf import settings
from django.test import TestCase

from card_generator.cards.client import QueueCardsClient
from card_generator.cards.tests.mixins import OpenSPPClientTestMixin
from card_generator.tasks.cards import perform_merging


class TestMergeCardTask(OpenSPPClientTestMixin, TestCase):
    @mock.patch(
        "card_generator.cards.client.QueueCardsClient.update_queue_batch_record"
    )
    @mock.patch("card_generator.cards.client.QueueCardsClient.get_id_queue_pdfs")
    @mock.patch("card_generator.cards.client.QueueCardsClient.get_queue_batch")
    def test_merge_card(
        self,
        mock_get_queue_batch,
        mock_get_id_queue_pdfs,
        mock_update_queue_batch_record,
    ):
        mock_get_queue_batch.return_value = self.sample_queue_batch
        mock_get_id_queue_pdfs.return_value = [
            self.sample_id_queue,
            self.sample_id_queue,
        ]
        mock_update_queue_batch_record.return_value = [self.sample_queue_batch]
        client = QueueCardsClient(
            server_root=settings.OPENSPP_SERVER_ROOT,
            username=settings.OPENSPP_USERNAME,
            password=settings.OPENSPP_API_TOKEN,
            db_name=settings.OPENSPP_DB_NAME,
        )
        perform_merging(client, 1)

    @mock.patch("card_generator.cards.client.logger")
    @mock.patch("card_generator.cards.client.QueueCardsClient.get_queue_batch")
    def test_merge_card_no_id_queue(self, mock_get_queue_batch, mock_logger):
        mock_get_queue_batch.return_value = {"name": "no_id_queue", "id": 1}
        client = QueueCardsClient(
            server_root=settings.OPENSPP_SERVER_ROOT,
            username=settings.OPENSPP_USERNAME,
            password=settings.OPENSPP_API_TOKEN,
            db_name=settings.OPENSPP_DB_NAME,
        )
        perform_merging(client, 1)
        mock_logger.info.assert_called_with("Batch ID 1 don't have queue IDs.")

    @mock.patch("card_generator.tasks.cards.logger")
    @mock.patch("card_generator.cards.client.QueueCardsClient.get_queue_batch")
    def test_merge_card_no_queue_batch(self, mock_get_queue_batch, mock_logger):
        mock_get_queue_batch.return_value = None
        client = QueueCardsClient(
            server_root=settings.OPENSPP_SERVER_ROOT,
            username=settings.OPENSPP_USERNAME,
            password=settings.OPENSPP_API_TOKEN,
            db_name=settings.OPENSPP_DB_NAME,
        )
        perform_merging(client, 1)
        mock_logger.info.assert_called_with("Batch ID 1 has an empty record.")
