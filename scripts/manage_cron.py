#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from crontab import CronTab

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUN_SCRIPT = PROJECT_ROOT / "scripts" / "run.sh"
CRON_COMMENT = "trade.monitor"


def get_cron():
    try:
        return CronTab(user=True)
    except Exception as e:
        print(f"Error accessing crontab: {e}")
        sys.exit(1)


def add_job(interval_min=1):
    cron = get_cron()
    cron.remove_all(comment=CRON_COMMENT)

    job = cron.new(command=f"/bin/bash {RUN_SCRIPT}", comment=CRON_COMMENT)
    job.minute.every(interval_min)

    cron.write()
    print(f"Cron job added: runs every {interval_min} minute(s)")
    print(f"Command: /bin/bash {RUN_SCRIPT}")


def remove_job():
    cron = get_cron()
    count = cron.remove_all(comment=CRON_COMMENT)
    cron.write()
    if count > 0:
        print(f"Removed {count} cron job(s) with comment '{CRON_COMMENT}'.")
    else:
        print(f"No cron jobs found with comment '{CRON_COMMENT}'.")


def list_jobs():
    cron = get_cron()
    jobs = list(cron.find_comment(CRON_COMMENT))
    if not jobs:
        print(f"No cron jobs found with comment '{CRON_COMMENT}'.")
        return

    print(f"Cron jobs for '{CRON_COMMENT}':")
    for job in jobs:
        print(f"  {job}")


def main():
    parser = argparse.ArgumentParser(description="Manage cron jobs for trade.monitor")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    add_parser = subparsers.add_parser("add", help="Add or update the cron job")
    add_parser.add_argument(
        "--interval", type=int, default=1, help="Interval in minutes (default: 1)"
    )

    subparsers.add_parser("remove", help="Remove the cron job")
    subparsers.add_parser("list", help="List the cron jobs")

    args = parser.parse_args()

    if args.command == "add":
        add_job(args.interval)
    elif args.command == "remove":
        remove_job()
    elif args.command == "list":
        list_jobs()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
