import logging
import tempfile

from celery import shared_task
from django.conf import settings
from PyPDF2 import PdfMerger

from card_generator.cards.client import QueueCardsClient
from card_generator.cards.utils import convert_file_to_uri, data_uri_to_file

logger = logging.getLogger()


def get_pdfs(client: QueueCardsClient, batch_id: int):

    raw_pdfs = client.get_id_queue_pdfs(batch_id)
    return [item["id_pdf"] for item in raw_pdfs]


def save_pdf_to_openspp(client: QueueCardsClient, batch_id: int, pdf_uri: str):
    data = {"id_pdf": pdf_uri}
    client.update_queue_batch_record(batch_id=batch_id, data=data)


def merge_pdf(list_of_pdf: list, target_dir: str):
    file_name = f"{target_dir}/result.pdf"
    with PdfMerger() as merger:
        for item in list_of_pdf:
            merger.append(item)
        merger.write(file_name)

    return file_name


def perform_merging(client: QueueCardsClient, batch_id: int):
    with tempfile.TemporaryDirectory() as temp_dir:
        list_of_files = get_pdfs(client=client, batch_id=batch_id)
        if not list_of_files:
            logger.info(f"Batch ID #{batch_id} have no cards available.")
            return
        file_list = data_uri_to_file(list_of_files, temp_dir)

        result_pdf = merge_pdf(file_list, temp_dir)
        _, base64_pdf = convert_file_to_uri("application/pdf", result_pdf).split(",")
        save_pdf_to_openspp(
            client=client,
            batch_id=batch_id,
            pdf_uri=base64_pdf,
        )


@shared_task
def merge_cards(batch_id: int):
    client = QueueCardsClient(
        server_root=settings.OPENSPP_SERVER_ROOT,
        username=settings.OPENSPP_USERNAME,
        password=settings.OPENSPP_API_TOKEN,
        db_name=settings.OPENSPP_DB_NAME,
    )
    perform_merging(client, batch_id)
    logger.info(f"Batch #{batch_id} have been updated with merged cards.")
