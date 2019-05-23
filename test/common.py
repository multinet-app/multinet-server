import json
import requests


WORKSPACE = 'test-multinet'

graphql_url = 'http://localhost:9090/api/v1/multinet/graphql'


def multinet_request(query):
    r = requests.post(graphql_url, data=json.dumps({'query': query}))
    return r.json()


def delete_workspace(name):
    query = f'''mutation {{
        deleteWorkspace(name: "{name}")
    }}'''

    return multinet_request(query)
