"""Download Les Miserables data from the web and process it into Multinet CSV files."""

import csv
import json
import sys


def add_key(rec, idx):
    """Add a key value to the character records."""

    rec["_key"] = idx
    return rec


def convert_link(link):
    """Convert the D3 JSON link data into a Multinet-style record."""

    return {
        "_from": f"""characters/{link["source"]}""",
        "_to": f"""characters/{link["target"]}""",
        "value": link["value"],
    }


def write_csv(data, fields, filename):
    """Write a CSV file from data and field names."""

    with open(filename, "w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)

        writer.writeheader()
        for row in data:
            writer.writerow(row)


def main():
    """Run main function."""

    data = json.loads(sys.stdin.read())

    # Prepare the node data by adjoining a key value equal to each record's
    # index in the original data.
    nodes = [add_key(record, index) for (index, record) in enumerate(data["nodes"])]

    # Convert the link data to Multinet form. Note that the D3 JSON format uses
    # node list indices to refer to the source and target nodes; these can be
    # used unchanged because of how the key value for the nodes was set above.
    links = [convert_link(link) for link in data["links"]]

    # Write out both the node and link data to CSV files.
    write_csv(nodes, ["_key", "name", "group"], "characters.csv")
    write_csv(links, ["_from", "_to", "value"], "relationships.csv")

    return 0


if __name__ == "__main__":
    sys.exit(main())
