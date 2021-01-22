"""Download Les Miserables data from the web and process it into Multinet CSV files."""

import csv
import json
import sys


def add_key(rec, idx):
    """Add a key value to the character records."""

    rec["_key"] = rec["id"]
    rec["influential"] = "false" if rec["influential"] == "False" else "true"
    rec["original"] = "false" if rec["original"] == "False" else "true"

    del rec["utc_offset"]
    del rec["id"]

    return rec


def convert_link(link, idx):
    """Convert the D3 JSON link data into a Multinet-style record."""

    return {
        "_key": str(idx),
        "_from": f"""people/{link["source"]}""",
        "_to": f"""people/{link["target"]}""",
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
    links = [convert_link(link, index) for (index, link) in enumerate(data["links"])]

    # Reduce the total number of nodes by truncating
    nodes = [nodes[i] for i in range(0, 100)]

    # Filter links to those with both in node table
    links = [
        link
        for link in links
        if (
            any(f"people/{node['_key']}" == link["_from"] for node in nodes)
            and any(f"people/{node['_key']}" == link["_to"] for node in nodes)
        )
    ]
    links = [link for (index, link) in enumerate(links) if index % 10 == 0]

    # Write out both the node and link data to CSV files.
    write_csv(
        nodes,
        [
            "_key",
            "followers_count",
            "query_tweet_count",
            "friends_count",
            "statuses_count",
            "listed_count",
            "favourites_count",
            "count_followers_in_query",
            "screen_name",
            "profile_image_url",
            "influential",
            "original",
        ],
        "people.csv",
    )
    write_csv(links, ["_key", "_from", "_to"], "connections.csv")

    return 0


if __name__ == "__main__":
    sys.exit(main())
