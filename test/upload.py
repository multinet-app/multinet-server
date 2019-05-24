from pprint import pprint
import sys

from common import create_workspace, upload_csv, WORKSPACE


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
            error_msg(result.json())
            sys.exit(1)
    print('tables uploaded successfully')
