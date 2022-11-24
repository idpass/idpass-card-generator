import logging
import xmlrpc.client
from typing import Any, Literal, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class OpenSPPAPIException(Exception):
    pass


class OpenSPPClient:
    COMMON_ENDPOINT = "/xmlrpc/2/common"
    MODEL_ENDPOINT = "/xmlrpc/2/object"
    FOOD_AGENT_MODEL = "spp.service.point"

    def __init__(self, server_root: str, username: str, password: str, db_name: str):
        """Initialize a OpenSPP client.

        :param server_root: OpenSPP root url. E.g: https://dev.newlogic-demo.com/
        :param username: User's username with access to the server
        :param password: User's password or API key with access to the server
        :param db_name: Name of database that contains the data for query
        :return: a OpenSPPClient instance.
        """
        self.server_root = server_root
        self.username = username
        self.password = password
        self.db_name = db_name
        self.uid = self.login(username, password)

    @staticmethod
    def get_server_proxy(url):
        return xmlrpc.client.ServerProxy(url)

    def login(self, username, password, kwargs: Optional[dict] = None):
        if not kwargs:
            kwargs = {}
        common_endpoint = self.get_server_proxy(
            f"{self.server_root}{self.COMMON_ENDPOINT}"
        )
        return common_endpoint.authenticate(self.db_name, username, password, kwargs)

    def call_api(
        self,
        method_name: Literal["fetch", "read", "update", "write"],
        model_name: str,
        paginated: bool = True,
        item_ids: list[int] | None = None,
        query_params: list | None = None,
        result_params: dict | None = None,
        data: dict | None = None,
        related_data: dict | None = None,
    ):
        """
        :param method_name: Method to be used in query
        :param model_name: Name of model to do the query
        :param paginated: Run fetch query in batches if set to True
        :param item_ids: List of ids to be used in query
        :param query_params: A list of filters to records. Ex. [['field_name', '=', True], ['field_name_2', '=', False]]
        :param result_params: A dictionary of parameters to manage results.
            Ex. {"fields": ["name"], "limit": 5, "offset": 2}
        :param data: A dictionary of data for updating or creating new record. Ex. {"name": "New Updated Test Name"}
        :param related_data: A dictionary of related fields to prefetch
            Ex. {"company_id": ["id", "name", {"currency_id": ["id", "name", "symbol"]}],}
        To get all fields of the related model, we can use "__all__", E.g: {"company_id": ["__all__"]}
        """
        if paginated and method_name == "fetch":
            method_name = "paginated_fetch"

        query_method = getattr(self, f"_{method_name}")
        response = query_method(
            model_name=model_name,
            item_ids=item_ids,
            query_params=query_params,
            result_params=result_params,
            data=data,
            related_data=related_data,
        )
        return response

    def _get_fields(self, model_name, attributes: list | None = None):
        # TODO: It would be better if we can cache the results here for the same model
        if not attributes:
            attributes = []

        return self._run_query(
            model_name=model_name,
            method_name="fields_get",
            query_params=[[]],
            result_params={"attributes": attributes},
        )

    def _sanitize_data(self, model_name: str, data: list, to_openspp: bool = False):
        """
        :param to_openspp: True if the data will be used as a payload to OpenSPP,
            False if the data will be used within the project.
        """
        attributes = ["type"]
        fields = self._get_fields(model_name=model_name, attributes=attributes)
        source_value, target_value = (None, False) if to_openspp else (False, None)

        for item in data:
            if not fields.items():
                continue
            # Change all non-boolean fields value 'False' to None
            for key, value in fields.items():
                if key not in item:
                    continue
                if value["type"] != "boolean" and item.get(key) is source_value:
                    item[key] = target_value
        return data

    def _get_related_data(
        self, records: list[dict], model_name, related_data: dict
    ) -> list[dict]:
        """Get related data for the given records."""
        # TODO: Add more tests to cover all the code paths of this method
        if not records:
            return records

        attributes = ["relation", "type"]
        model_relations = self._get_fields(model_name=model_name, attributes=attributes)
        record_fields = list(records[0].keys())

        # Convert many2one fields from a list of id and __str__ into a dict
        for foreign_key in model_relations:
            if (
                foreign_key not in record_fields
                or model_relations[foreign_key]["type"] != "many2one"
            ):
                continue
            for record in records:
                if record[foreign_key]:
                    record[foreign_key] = {
                        "id": record[foreign_key][0],
                        "__str__": record[foreign_key][1],
                    }

        for foreign_key in related_data:
            if (
                foreign_key not in record_fields
                or "relation" not in model_relations.get(foreign_key, {})
            ):
                continue
            fields = related_data[foreign_key]

            # Extract nested related data and the field names of the related model
            nested_related_data = {}
            field_names = []
            for item in fields:
                if isinstance(item, str):
                    field_names.append(item)
                if isinstance(item, dict):
                    field_names.extend(item.keys())
                    for k, v in item.items():
                        nested_related_data[k] = v

            related_data_model_name = model_relations[foreign_key]["relation"]
            foreign_key_values = list(
                {record[foreign_key]["id"] for record in records if record[foreign_key]}
            )
            query_params = [[["id", "in", foreign_key_values]]]
            if field_names != ["__all__"]:
                result_params = {"fields": field_names}
            else:
                result_params = {}
            # Fetch the related data for the foreign_key
            related_records = self._fetch(
                model_name=related_data_model_name,
                query_params=query_params,
                result_params=result_params,
                related_data=nested_related_data,
            )
            # Update the related data for all records
            related_record_by_foreign_key_value = {
                related_record["id"]: related_record
                for related_record in related_records
            }
            for record in records:
                if record[foreign_key]:
                    record[foreign_key] = related_record_by_foreign_key_value[
                        record[foreign_key]["id"]
                    ]

        return records

    def _read(
        self,
        model_name: str,
        item_ids: list[int],
        result_params: dict | None = None,
        *args,
        **kwargs,
    ):
        result = self._run_query(model_name, "read", [item_ids], result_params)
        if not result:
            raise OpenSPPAPIException(
                f"Records with IDs#{', '.join([str(idx) for idx in item_ids])} does not exists."
            )
        return self._sanitize_data(model_name, result)

    def _fetch(
        self,
        model_name: str,
        query_params: list | None = None,
        result_params: dict | None = None,
        related_data: dict | None = None,
        *args,
        **kwargs,
    ):
        result = self._run_query(model_name, "search_read", query_params, result_params)
        sanitized_result = self._sanitize_data(model_name, result)
        self._get_related_data(
            records=sanitized_result,
            model_name=model_name,
            related_data=related_data or {},
        )
        return sanitized_result

    def _paginated_fetch(
        self,
        model_name: str,
        query_params: list | None = None,
        result_params: dict | None = None,
        related_data: dict | None = None,
        *args,
        **kwargs,
    ):
        fetch_count = self._run_query(model_name, "search_count", query_params, {})
        default_fetch_limit = settings.OPENSPP_DEFAULT_FETCH_LIMIT
        if not result_params:
            result_params = {
                "limit": default_fetch_limit,
                "offset": 0,
            }
        elif "limit" not in result_params:
            result_params["limit"] = default_fetch_limit
            result_params["offset"] = 0

        fetched_data = []
        batch_repetition = (fetch_count - 1) // default_fetch_limit + 1
        for _ in range(0, batch_repetition):
            result = self._fetch(
                model_name, query_params, result_params, related_data=related_data
            )
            fetched_data.extend(result)
            result_params["offset"] += default_fetch_limit
        return fetched_data

    def _update(
        self,
        model_name: str,
        item_ids: list[int],
        data: dict,
        result_params: dict | None = None,
        *args,
        **kwargs,
    ):
        cleaned_data = self._sanitize_data(
            model_name=model_name, data=[data], to_openspp=True
        )
        try:
            result = self._run_query(
                model_name=model_name,
                method_name="write",
                query_params=[item_ids, cleaned_data[0]],
                result_params=result_params,
            )
        except xmlrpc.client.Fault as e:
            server_message = e.faultString
            raise OpenSPPAPIException(
                f"Something went wrong. Remote server raise an error with logs. Log: {server_message}"
            )
        if not result:
            raise OpenSPPAPIException("Updating data failed.")
        return self._read(model_name, item_ids, result_params)

    def _run_query(
        self,
        model_name: str,
        method_name: str,
        query_params: Any | None = None,
        result_params: Any | None = None,
    ):
        server = self.get_server_proxy(f"{self.server_root}{self.MODEL_ENDPOINT}")
        if not result_params:
            result_params = {}
        if query_params is None or query_params == []:
            query_params = [[]]
        return server.execute_kw(
            self.db_name,
            self.uid,
            self.password,
            model_name,
            method_name,
            query_params,
            result_params,
        )


class QueueCardsClient(OpenSPPClient):
    def get_queue_batch(self, batch_id: int):
        return self.call_api(
            "fetch",
            model_name=settings.OPENSPP_QUEUE_BATCH_MODEL,
            query_params=[[["id", "=", batch_id]]],
            result_params={"fields": ["queued_ids"]},
        )

    def get_id_queue_pdfs(self, batch_id: int):
        record = self.get_queue_batch(batch_id=batch_id)

        if not record:
            logger.info(f"Batch ID {batch_id} has an empty record.")
            return []
        id_queue_ids = record[0].get("queued_ids", [])
        if not id_queue_ids:
            logger.info(f"Batch ID {batch_id} don't have queue IDs.")
            return []

        return self.call_api(
            "fetch",
            model_name=settings.OPENSPP_ID_QUEUE_MODEL,
            query_params=[[["id", "in", id_queue_ids]]],
            result_params={"fields": ["id_pdf"]},
        )

    def update_queue_batch_record(self, batch_id: int, data: dict):
        try:
            response = self.call_api(
                method_name="update",
                model_name=settings.OPENSPP_QUEUE_BATCH_MODEL,
                query_params=[[["id", "=", batch_id]]],
                item_ids=[batch_id],
                data=data,
            )
        except xmlrpc.client.Fault as e:
            logger.info(f"Error in updating batch ID {batch_id}")
            logger.info(e.faultString)
            return
        return response
