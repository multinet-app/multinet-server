import json
import requests


WORKSPACE = 'test-multinet'

girder_url = 'http://localhost:9090/api/v1/multinet'
graphql_url = f'{girder_url}/graphql'
csv_url = f'{girder_url}/csv'


def multinet_request(query):
    return requests.post(graphql_url, data=json.dumps({'query': query}))


def delete_workspace(name):
    return multinet_request(f'''mutation {{
        deleteWorkspace(name: "{name}")
    }}''')


def create_workspace(name):
    return multinet_request(f'''mutation {{
        workspace(name: "{name}")
    }}''')


def upload_csv(filename, workspace, table):
    with open(filename) as f:
        raw = f.read()

    return requests.post(f'{csv_url}/{workspace}/{table}', data=raw)
