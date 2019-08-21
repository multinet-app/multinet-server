"""Convert raw Boston club membership data into CSV."""

import csv
import string
import sys


def namify_member(name):
    """Convert data formatted name into human readable form."""
    [last_name, first_name] = map(lambda s: s.capitalize(), name.split("."))
    return " ".join([first_name, last_name])


def namify_club(name):
    """Convert data formmated club name into human readable form."""

    def split_on(s, splitters):
        if not s:
            return []

        for (i, c) in enumerate(s[1:]):
            if c in splitters:
                return [s[: i + 1]] + split_on(s[i + 1 :], splitters)

        return [s]

    return " ".join(split_on(name, string.ascii_uppercase))


if __name__ == "__main__":
    # Read in the raw data.
    raw_data = list(map(dict, csv.DictReader(sys.stdin)))

    # Extract the club and member names.
    club_names = [k for k in raw_data[0] if k]
    member_names = [row[""] for row in raw_data]

    # Construct tables to a unique ID for each entity.
    ids = {name: idx for (idx, name) in enumerate(club_names + member_names)}

    # Create member and club tables.
    members = [
        {"_key": ids[name], "name": namify_member(name)} for name in member_names
    ]
    clubs = [{"_key": ids[name], "name": namify_club(name)} for name in club_names]

    # Create the membership table.
    membership = []
    for row in raw_data:
        member_name = row[""]
        club_names = [club_name for club_name in row if row[club_name] == "1"]

        for club_name in club_names:
            membership.append(
                {
                    "_from": f"members/{ids[member_name]}",
                    "_to": f"clubs/{ids[club_name]}",
                }
            )

    # Dump the tables to disk as csv files.
    for table_name in ["clubs", "members", "membership"]:
        csvname = f"{table_name}.csv"
        table = eval(table_name)

        with open(csvname, "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=list(table[0]))

            writer.writeheader()
            for row in table:
                writer.writerow(row)
