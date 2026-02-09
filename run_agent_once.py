import json
from agent import InventoryAgent

if __name__ == '__main__':
    agent = InventoryAgent()
    result = agent.run_check()
    print(json.dumps(result, indent=2))
