"""Repair the stock airport flights data so it works properly with Multinet."""

import csv
import sys


def main():
    """Run main function."""

    reader = csv.DictReader(sys.stdin)
    writer = csv.DictWriter(sys.stdout, reader.fieldnames)

    writer.writeheader()
    for row in reader:
        # Prepend the presumed node table name to the from/to columns.
        row["_from"] = f'airports/{row["_from"]}'
        row["_to"] = f'airports/{row["_to"]}'

        writer.writerow(row)

    return 0


if __name__ == "__main__":
    sys.exit(main())
