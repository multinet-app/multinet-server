from arango import ArangoClient
import getpass
import sys

from mypy_extensions import TypedDict


HostAnalysis = TypedDict(
    "HostAnalysis", {"protocol": str, "hostname": str, "port": int}
)


def analyze_host(host: str) -> HostAnalysis:
    if host[:8] == "https://":
        protocol = "https"
    elif host[:7] == "http://":
        protocol = "http"
    else:
        print(f"bad protocol: {host}", file=sys.stderr)
        raise RuntimeError

    parts = host[len(f"{protocol}://") :].split(":")
    hostname = parts[0]

    try:
        port = int(parts[1])
    except IndexError:
        port = 8529
    except ValueError:
        print(f"bad port: {parts[1]}", file=sys.stderr)
        raise RuntimeError

    return {"protocol": protocol, "hostname": hostname, "port": port}


def main():
    if len(sys.argv) < 2:
        print("usage: ensure_workspace_metadata.py <arango-host>", file=sys.stderr)
        return 1

    # Split apart the host parameter into constituents.
    try:
        args = analyze_host(sys.argv[1])
    except RuntimeError:
        return 1

    # Create a connection to the database.
    client = ArangoClient(
        protocol=args["protocol"], host=args["hostname"], port=args["port"]
    )

    # Get a password from the user.
    password = getpass.getpass("Password: ")

    # Retrieve the workspace mapping collection from the system database.
    db = client.db(name="_system", password=password)
    coll = db.collection("workspace_mapping")

    # Loop through the documents and correct ones with a missing "permissions"
    # field.
    for doc in coll.all():
        if "permissions" not in doc:
            doc["permissions"] = {
                "owner": "",
                "maintainers": [],
                "writers": [],
                "readers": [],
                "public": True,
            }

            print(f"updating {doc['name']}...", end="")
            db.update_document(doc)
            print("done")


if __name__ == "__main__":
    sys.exit(main())
