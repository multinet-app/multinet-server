import sys

from common import delete_workspace, WORKSPACE


if __name__ == "__main__":
    print(f'deleting workspace "{WORKSPACE}"...')

    result = delete_workspace(WORKSPACE).json()

    if result["errors"]:
        print("errors encountered:\n", *result["errors"], sep="\n")
        sys.exit(1)

    success = result["data"]["deleteWorkspace"] is not None
    if success:
        print("deleted succesfully")
        sys.exit(0)
    else:
        print(f"workspace {WORKSPACE} does not exist")
        sys.exit(1)
