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


def create_graph(workspace, name):
    return multinet_request(f'''mutation {{
        graph(workspace: "{workspace}", name: "{name}") {{
            name
            nodeTypes {{
                name
                properties {{
                    label
                    table
                    key
                }}
            }}
            edgeTypes {{
                name
                properties {{
                    label
                    table
                    key
                }}
            }}
        }}
    }}''')


def create_type(workspace, graph, table, properties):
    propertyArg = ', '.join(['{{label: "{0}", table: "{1}", key: "{2}"}}'.format(prop['label'], prop['table'], prop['key']) for prop in properties])

    return multinet_request(f'''mutation {{
        entityType(workspace: "{workspace}", graph: "{graph}", table: "{table}", properties: [{propertyArg}]) {{
            name
            properties {{
                label
                table
                key
            }}
        }}
    }}''')


def upload_csv(filename, workspace, table):
    with open(filename) as f:
        raw = f.read()

    return requests.post(f'{csv_url}/{workspace}/{table}', data=raw)
