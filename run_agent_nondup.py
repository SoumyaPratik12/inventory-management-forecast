import os
import json
# Force dedupe window to 0 for this run
os.environ['DEDUPE_WINDOW_DAYS'] = '-1'

from agent import InventoryAgent

if __name__ == '__main__':
    agent = InventoryAgent()
    result = agent.run_check()
    print(json.dumps(result, indent=2))
