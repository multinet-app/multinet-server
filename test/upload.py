import sys

from common import create_workspace, WORKSPACE


if __name__ == '__main__':
    print(f'creating workspace "{WORKSPACE}"...')

    result = create_workspace(WORKSPACE)

    if result['errors']:
        print('errors encountered:\n', *result["errors"], sep='\n')
        sys.exit(1)
    else:
        print('created succesfully')
        sys.exit(0)
