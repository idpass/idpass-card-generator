import logging
import tempfile

from celery import shared_task
from django.conf import settings
from PyPDF2 import PdfMerger

from card_generator.cards.client import QueueCardsClient
from card_generator.cards.utils import convert_file_to_uri, data_uri_to_file

logger = logging.getLogger(__name__)


def get_pdfs(client: QueueCardsClient, batch_record: dict):
    if not batch_record:
        return []

    raw_pdfs = client.get_id_queue_pdfs(batch_record=batch_record)
    return [item["id_pdf"] for item in raw_pdfs]


def save_pdf_to_openspp(
    client: QueueCardsClient, batch_id: int, pdf_uri: str, filename: str
):
    data = {"id_pdf": pdf_uri, "merge_status": "merged", "id_pdf_filename": filename}
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
        batch_record = client.get_queue_batch(batch_id)
        if not batch_record:
            logger.info(f"Batch ID {batch_id} has an empty record.")
            return

        list_of_files = get_pdfs(client=client, batch_record=batch_record)
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
            filename=batch_record.get("name"),
        )


@shared_task(bind=True, max_retries=3)
def merge_cards(self, batch_id: int) -> None:
    """
    Merge cards of a Batch Queue from OpenSPP server.
    Process flow:
        - get the batch record to capture the name and queue IDs
        - get the PDFs of cards for each queue ID records
        - merge the PDFs into 1 PDF
        - push the merged PDF to Batch record's id_pdf field, update merge_status and add filename also
    :arg batch_id: ID of Batch record
    """
    try:
        client = QueueCardsClient(
            server_root=settings.OPENSPP_SERVER_ROOT,
            username=settings.OPENSPP_USERNAME,
            password=settings.OPENSPP_API_TOKEN,
            db_name=settings.OPENSPP_DB_NAME,
        )
    except Exception as e:  # noqa Lets catch all errors error for debugging and retry
        logger.info(f"Error raised on client. {str(e)}")
        self.retry(exc=e, countdown=30)
        return
    try:
        perform_merging(client, batch_id)
    except Exception as e:  # noqa Lets catch all errors error for debugging and retry
        logger.info(f"Error raised while performing merge. {str(e)}")
        data = {"merge_status": "error_merging"}
        client.update_queue_batch_record(batch_id=batch_id, data=data)
        self.retry(exc=e, countdown=30)
        return
    logger.info(f"Batch #{batch_id} have been updated with merged cards.")
