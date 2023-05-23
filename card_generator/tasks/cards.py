import logging
import tempfile
import xmlrpc.client

from celery import Task, shared_task
from django.conf import settings
from django.utils.timezone import now
from PyPDF2 import PdfMerger

from card_generator.cards.client import QueueCardsClient
from card_generator.cards.utils import convert_file_to_uri, data_uri_to_file

logger = logging.getLogger(__name__)


class OPENSPPCeleryTask(Task):
    max_retries = 3

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        batch_id = args[1]["batch_id"]
        data = {"merge_status": "error_merging"}
        try:
            client = QueueCardsClient(
                server_root=settings.OPENSPP_SERVER_ROOT,
                username=settings.OPENSPP_USERNAME,
                password=settings.OPENSPP_API_TOKEN,
                db_name=settings.OPENSPP_DB_NAME,
            )
        except Exception as e:  # noqa Lets catch all errors error for debugging
            logger.info(
                f"Error raised on client while updating batch {batch_id} status to failed. {str(e)}"
            )
            return
        try:
            client.update_queue_batch_record(batch_id=batch_id, data=data)
        except (
            xmlrpc.client.ProtocolError,
            xmlrpc.client.Fault,
            Exception,
        ) as e:  # noqa Lets catch all errors error for debugging
            logger.info(
                f"Error raised while updating batch {batch_id} failed status. {str(e)}"
            )
            return
        logger.info(f"Batch #{batch_id} have been updated with failed status.")


def get_pdfs(client: QueueCardsClient, batch_record: dict) -> list:
    """
    Get the cards from OpenSPP
    :param client: The client to use when communicating to OpenSPP API
    :param batch_record: ID of Batch record
    :return: List of PDFs to be merged
    """
    if not batch_record:
        return []

    raw_pdfs = client.get_id_queue_pdfs(batch_record=batch_record)
    return [item["id_pdf"] for item in raw_pdfs]


def save_pdf_to_openspp(
    client: QueueCardsClient, batch_id: int, pdf_uri: str, filename: str
) -> None:
    """
    Update OpenSPP with the merged PDF
    :param client: The client to use when communicating to OpenSPP API
    :param batch_id: ID of Batch record
    :param pdf_uri: URI formatted PDF
    :param filename: name of merged PDF
    """
    data = {
        "id_pdf": pdf_uri,
        "merge_status": "merged",
        "id_pdf_filename": filename,
        "date_merged": now().date().isoformat(),
    }
    client.update_queue_batch_record(batch_id=batch_id, data=data)


def merge_pdf(list_of_pdf: list, target_dir: str) -> str:
    """
    Merge the list of PDFs
    :param list_of_pdf: Lists of PDFs to be merged
    :param target_dir: Target directory where to save the merged PDF
    :return: The file name of the merged PDF
    """
    file_name = f"{target_dir}/result.pdf"
    with PdfMerger() as merger:
        for item in list_of_pdf:
            merger.append(item)
        merger.write(file_name)

    return file_name


def perform_merging(client: QueueCardsClient, batch_id: int) -> None:
    """
    Do the actual process of merging the cards.
    :param client: The client to use when communicating to OpenSPP API
    :param batch_id: ID of Batch record
    """
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


@shared_task(bind=True, base=OPENSPPCeleryTask)
def merge_cards(self, batch_id: int) -> None:
    """
    Merge cards of a Batch Queue from OpenSPP server.
    Process flow:
        - get the batch record to capture the name and queue IDs
        - get the PDFs of cards for each queue ID records
        - merge the PDFs into 1 PDF
        - push the merged PDF to Batch record's id_pdf field, update merge_status and add filename also
    :param batch_id: ID of Batch record
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
        raise self.retry(exc=e, countdown=30)
    try:
        perform_merging(client, batch_id)
    except (
        xmlrpc.client.ProtocolError,
        xmlrpc.client.Fault,
        Exception,
    ) as e:  # noqa Lets catch all errors error for debugging and retry
        logger.info(f"Error raised while performing merge. {str(e)}")
        raise self.retry(countdown=30)
    logger.info(f"Batch #{batch_id} have been updated with merged cards.")
