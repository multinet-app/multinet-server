from pprint import pprint
import sys

from common import create_workspace, create_graph, create_type, upload_csv, WORKSPACE


def error_message(msg):
    print('error:')
    print(msg)


if __name__ == '__main__':
    # Create the workspace.
    print(f'creating workspace "{WORKSPACE}"...')

    result = create_workspace(WORKSPACE)
    response = result.json()

    if response['errors']:
        print('errors encountered:\n', *response["errors"], sep='\n')
        sys.exit(1)
    else:
        print('created succesfully')

    # Upload the data tables.
    for table in ['members', 'member_data', 'clubs', 'club_data', 'membership']:
        print(f'uploading {table}...')
        result = upload_csv(f'data/{table}.csv', WORKSPACE, table)
        if result.status_code != 200:
            error_message(result.json())
            sys.exit(1)
    print('tables uploaded successfully')

    # Create the graph.
    print('creating graph...')
    graph = create_graph(WORKSPACE, 'boston')
    pprint(graph.json())

    # Define the node data types.
    props = [
        {'label': 'name',
         'table': 'members',
         'key': 'name'},
        {'label': 'name_length',
         'table': 'member_data',
         'key': 'name_length'}
    ]
    types = create_type(WORKSPACE, 'boston', 'members', props)
    pprint(types.json())
