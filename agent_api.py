#!/usr/bin/env python3
"""
INVENTORY AGENT API
==================
RESTful API for agent integration
"""

from fastapi import FastAPI, BackgroundTasks
from agent import InventoryAgent
import uvicorn
import threading

app = FastAPI(title="Inventory Agent API", version="1.0.0")
agent = InventoryAgent(check_interval=300)  # 5 minutes
agent_thread = None


@app.post("/agent/start")
async def start_agent(background_tasks: BackgroundTasks):
    """Start the inventory agent"""
    global agent_thread

    if agent.running:
        return {"message": "Agent already running", "status": "running"}

    def run_agent():
        agent.start()

    agent_thread = threading.Thread(target=run_agent, daemon=True)
    agent_thread.start()

    return {"message": "Agent started", "status": "starting"}


@app.post("/agent/stop")
async def stop_agent():
    """Stop the inventory agent"""
    agent.stop()
    return {"message": "Agent stopped", "status": "stopped"}


@app.get("/agent/status")
async def get_agent_status():
    """Get agent status"""
    return agent.get_status()


@app.post("/agent/check")
async def manual_check():
    """Trigger manual check"""
    try:
        result = agent.sentinel.run_analysis()
        if result.get('alert_message'):
            agent.handle_alert(result)
        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/agent/alerts")
async def get_alerts():
    """Get recent alerts"""
    try:
        with open("alerts.json", "r") as f:
            alerts = [eval(line.strip())
                      for line in f.readlines()[-10:]]  # Last 10 alerts
        return {"alerts": alerts}
    except FileNotFoundError:
        return {"alerts": []}

if __name__ == "__main__":
    print("🤖 INVENTORY AGENT API")
    print("=" * 30)
    print("Endpoints:")
    print("  POST /agent/start   - Start agent")
    print("  POST /agent/stop    - Stop agent")
    print("  GET  /agent/status  - Get status")
    print("  POST /agent/check   - Manual check")
    print("  GET  /agent/alerts  - Get alerts")
    print("=" * 30)

    uvicorn.run(app, host="0.0.0.0", port=5004)
