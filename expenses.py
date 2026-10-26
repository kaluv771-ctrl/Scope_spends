"""
Simple expense tracker (CSV + date/time).

Usage:
    python expenses.py add                  # record a new expense (prompts for details)
    python expenses.py daily                # today's items and total
    python expenses.py daily 2026-10-24     # items and total for a specific day
    python expenses.py weekly               # this week's items and total (Mon-Sun)
    python expenses.py weekly 2026-10-20    # the week containing that date
    python expenses.py total                # grand total of all expenses
"""

import csv
import sys
from datetime import datetime, date, timedelta

FILE_NAME = "expenses.csv"
FIELDS = ["date", "time", "description", "amount"]
DATE_FMT = "%Y-%m-%d"
TIME_FMT = "%H:%M:%S"


# --- Part 1: Record an expense ---
def add_expense():
    description = input("Expense description: ").strip()
    amount_text = input("Amount in naira: ").strip()

    if not description:
        print("Description is required.")
        return

    try:
        amount = float(amount_text)
        if amount < 0:
            raise ValueError("Amount cannot be negative.")
    except ValueError:
        print("Enter a valid non-negative amount.")
        return

    now = datetime.now()
    row = {
        "date": now.strftime(DATE_FMT),
        "time": now.strftime(TIME_FMT),
        "description": description,  # csv module handles commas/quotes safely
        "amount": f"{amount:.2f}",
    }

    # Write the header only if the file is new or empty
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            needs_header = f.read(1) == ""
    except FileNotFoundError:
        needs_header = True

    with open(FILE_NAME, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if needs_header:
            writer.writeheader()
        writer.writerow(row)

    print(f"Expense saved on {row['date']} at {row['time']}.")


# --- Part 2: Read expenses back ---
def load_expenses():
    """Return a list of (datetime, description, amount); skip invalid rows."""
    expenses = []
    try:
        with open(FILE_NAME, "r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    when = datetime.strptime(f"{row['date']} {row['time']}",
                                             f"{DATE_FMT} {TIME_FMT}")
                    amount = float(row["amount"])
                except (ValueError, KeyError, TypeError):
                    print("Skipping invalid row:", row)
                    continue
                expenses.append((when, row["description"], amount))
    except FileNotFoundError:
        print("No expense file exists yet.")
    return expenses


def print_report(title, start, end):
    """Print every item between start and end (inclusive dates) and the total."""
    items = [e for e in load_expenses() if start <= e[0].date() <= end]
    items.sort(key=lambda e: e[0])

    print(f"\n{title}")
    print("-" * 60)
    if not items:
        print("No expenses recorded for this period.")
        return

    total = 0.0
    current_day = None
    for when, desc, amount in items:
        if when.date() != current_day:          # group by day (useful for weekly)
            current_day = when.date()
            print(f"\n{current_day.strftime('%A, %d %B %Y')}")
        print(f"  {when.strftime('%H:%M')}  {desc:<35} N{amount:>12,.2f}")
        total += amount

    print("-" * 60)
    print(f"{len(items)} item(s)   TOTAL: N{total:,.2f}\n")


def parse_date(args):
    if len(args) > 2:
        return datetime.strptime(args[2], DATE_FMT).date()
    return date.today()


def main():
    args = sys.argv
    command = args[1].lower() if len(args) > 1 else "add"

    try:
        if command == "add":
            add_expense()
        elif command == "daily":
            day = parse_date(args)
            print_report(f"Daily expenses - {day}", day, day)
        elif command == "weekly":
            day = parse_date(args)
            monday = day - timedelta(days=day.weekday())
            sunday = monday + timedelta(days=6)
            print_report(f"Weekly expenses - {monday} to {sunday}", monday, sunday)
        elif command == "total":
            print_report("All expenses", date.min, date.max)
        else:
            print(__doc__)
    except ValueError:
        print("Dates must be in YYYY-MM-DD format, e.g. 2026-10-24")


if __name__ == "__main__":
    main()
