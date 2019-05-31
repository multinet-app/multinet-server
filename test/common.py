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


def create_graph(workspace, name, node_tables, edge_table):
    return multinet_request(f'''mutation {{
        graph(workspace: "{workspace}", name: "{name}", node_tables: {json.dumps(node_tables)}, edge_table: "{edge_table}") {{
            name
        }}
    }}''')


def graph_nodes(workspace, name, node_type=None, key=None, search=None):
    node_type_arg = f'nodeType: "{node_type}"' if node_type else ''
    key_arg = f'key: "{key}"' if key else ''
    search_arg = f'search: "{search}"' if search else ''

    all_args = ', '.join(filter(None, [node_type_arg, key_arg, search_arg]))
    if all_args:
        all_args = f'({all_args})'

    return multinet_request(f'''query {{
        graph(workspace: "{workspace}", name: "{name}") {{
            nodes{all_args} {{
                total
                data(offset: 0, limit: 10) {{
                    key
                    properties (keys: ["name"]) {{
                        value
                    }}
                }}
            }}
        }}
    }}''')


def graph_edges(workspace, name, key=None, search=None):
    key_arg = f'key: "{key}"' if key else ''
    search_arg = f'search: "{search}"' if search else ''

    all_args = ', '.join(filter(None, [key_arg, search_arg]))
    if all_args:
        all_args = f'({all_args})'

    return multinet_request(f'''query {{
        graph(workspace: "{workspace}", name: "{name}") {{
            edges{all_args} {{
                total
                data(offset: 0, limit: 10) {{
                    key
                    properties {{
                        key
                        value
                    }}
                }}
            }}
        }}
    }}''')


def upload_csv(filename, workspace, table):
    with open(filename) as f:
        raw = f.read()

    return requests.post(f'{csv_url}/{workspace}/{table}', data=raw)
