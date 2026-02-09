#!/usr/bin/env python3
"""Inventory Sentinel CLI agent

Usage:
  python cli_agent.py once            # run a single check and print JSON
  python cli_agent.py once --no-dedupe # run single check ignoring dedupe
  python cli_agent.py run --interval 60 # run continuously (seconds)
"""
import argparse
import os
import json
import time
from datetime import datetime

from agent import InventoryAgent


def run_once(no_dedupe: bool = False):
    if no_dedupe:
        # disable dedupe by setting a negative window
        os.environ['DEDUPE_WINDOW_DAYS'] = '-1'

    agent = InventoryAgent()
    result = agent.run_check()
    print(json.dumps(result, indent=2))


def run_loop(interval: int = 300):
    agent = InventoryAgent(check_interval=interval)
    try:
        agent.start()
    except KeyboardInterrupt:
        agent.stop()


def main():
    parser = argparse.ArgumentParser(description='Inventory Sentinel CLI')
    sub = parser.add_subparsers(dest='cmd')

    p_once = sub.add_parser('once', help='Run a single check')
    p_once.add_argument('--no-dedupe', action='store_true', help='Ignore dedupe window')

    p_run = sub.add_parser('run', help='Run continuously')
    p_run.add_argument('--interval', type=int, default=300, help='Interval between checks in seconds')

    args = parser.parse_args()

    if args.cmd == 'once':
        run_once(no_dedupe=args.no_dedupe)
    elif args.cmd == 'run':
        run_loop(interval=args.interval)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
