"""Repair the stock airport flights data so it works properly with Multinet."""

import csv
import sys


def main():
    """Run main function."""

    with open(sys.argv[1]) as nodes:
        reader = csv.DictReader(nodes)
        ids = {n["_key"] for n in reader}

    reader = csv.DictReader(sys.stdin)
    writer = csv.DictWriter(sys.stdout, reader.fieldnames)

    writer.writeheader()
    for row in reader:
        # Filter out flights to or from undeclared airports.
        if row["_from"] in ids and row["_to"] in ids:
            # Prepend the presumed node table name to the from/to columns.
            row["_from"] = f'airports/{row["_from"]}'
            row["_to"] = f'airports/{row["_to"]}'

            writer.writerow(row)

    return 0


if __name__ == "__main__":
    sys.exit(main())
