from typing import Union

from common.utils.common import try_get_request


def op_join(fields, operator: str = 'AND'):
    """Joins an iterable by an operator."""
    return f" {operator} ".join(fields)


def solr_from_field_value(field: str, value: Union[str, list], operator: str = 'AND'):
    """Generates a generic SOLR string from a field and value item."""
    if isinstance(value, str):
        value = [value]
    joined_solr = op_join([f'{field}:{v}' for v in value], operator)

    return f'({joined_solr})'


def solr_from_records(records, exclude_fields=None):
    """Generates a SOLR string from a dictionary in key value format. Fields should have associated 'operator'
    field e.g., for 'type' you might have 'type_operator'."""
    solr_strs = []

    if not exclude_fields:
        exclude_fields = []

    for field, value in records.items():
        if field.endswith('_operator') or field in exclude_fields:
            # Skip operator fields
            continue

        operator = records.get(field + '_operator', 'AND')

        # Perform some array unpacking if necessary
        if isinstance(value, list) and len(value) == 1:
            value = value[0]

        if isinstance(operator, list) and len(operator) == 1:
            operator = operator[0]

        if not value or not operator:
            continue

        solr_str = solr_from_field_value(field, value, operator)
        solr_strs.append(solr_str)

    return op_join(solr_strs, 'AND')


class CKANAPI:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key

    def _make_request(self, endpoint, params=None):
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = self.api_key

        try:
            response = try_get_request(f"{self.base_url}/{endpoint}", params=params, headers=headers)
        except ConnectionError as e:
            raise Exception(f"Failed to fetch data from CKAN API.")

        return response.json()

    def group_list(self):
        """List all datasets on CKAN."""
        endpoint = 'api/3/action/group_list'
        return self._make_request(endpoint)

    def package_list(self):
        """List all datasets on CKAN."""
        endpoint = 'api/3/action/package_list'
        return self._make_request(endpoint)

    def package_show(self, dataset_id):
        """Get details of a specific dataset by ID."""
        endpoint = f'api/3/action/package_show'
        params = {'id': dataset_id}
        return self._make_request(endpoint, params=params)

    def package_search(self, query):
        """Search for datasets matching a specific query."""
        endpoint = 'api/3/action/package_search'
        return self._make_request(endpoint, params=query)

    def recent_data(self, query):
        endpoint = 'api/3/action/recently_changed_packages_activity_list'
        return self._make_request(endpoint, params=query)
