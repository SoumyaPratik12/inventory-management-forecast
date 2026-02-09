#!/usr/bin/env python3
"""
OPTIMIZED INVENTORY SENTINEL API
===============================
Lightweight FastAPI version with minimal dependencies
"""

from fastapi import FastAPI, HTTPException
import uvicorn
from optimized_sentinel import OptimizedInventorySentinel
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Optimized Inventory Sentinel",
    description="Streamlined inventory risk detection system",
    version="2.0.0"
)

# Initialize sentinel
sentinel = OptimizedInventorySentinel()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Optimized Inventory Sentinel",
        "version": "2.0.0",
        "status": "active",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/ingest")
async def ingest_data():
    """Ingest CSV data"""
    try:
        success = sentinel.ingest_data()
        if success:
            return {"message": "Data ingested successfully",
                    "timestamp": datetime.now().isoformat()}
        else:
            raise HTTPException(
                status_code=500,
                detail="Data ingestion failed")
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze")
async def run_analysis():
    """Run complete inventory analysis"""
    try:
        result = sentinel.run_analysis()
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/risks")
async def get_current_risks():
    """Get current risk assessments"""
    try:
        risks = sentinel.analyze_inventory()
        return {
            "timestamp": datetime.now().isoformat(),
            "total_risks": len(risks),
            "risks": [
                {
                    "sku": r.sku,
                    "cash_at_risk": round(r.cash_at_risk, 2),
                    "days_left": r.days_left,
                    "breakeven_prob": round(r.breakeven_prob, 3),
                    "urgency_score": round(r.urgency_score, 2)
                }
                for r in risks
            ]
        }
    except Exception as e:
        logger.error(f"Risk analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alert")
async def get_alert():
    """Get current alert message"""
    try:
        risks = sentinel.analyze_inventory()
        alert = sentinel.generate_alert(risks)
        return {
            "timestamp": datetime.now().isoformat(),
            "has_alert": alert is not None,
            "alert_message": alert,
            "risk_count": len(risks)
        }
    except Exception as e:
        logger.error(f"Alert generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Get system status"""
    try:
        # Quick database check
        with sentinel.get_connection() as conn:
            inventory_count = conn.execute(
                "SELECT COUNT(*) FROM inventory").fetchone()[0]
            sales_count = conn.execute(
                "SELECT COUNT(*) FROM sales").fetchone()[0]

        return {
            "timestamp": datetime.now().isoformat(),
            "system": "operational",
            "database": "connected",
            "inventory_items": inventory_count,
            "sales_records": sales_count
        }
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting Optimized Inventory Sentinel API")
    print("=" * 50)
    print("📍 Endpoints:")
    print("  • Health: http://localhost:5003/health")
    print("  • Status: http://localhost:5003/status")
    print("  • Analyze: http://localhost:5003/analyze")
    print("  • Risks: http://localhost:5003/risks")
    print("  • Alert: http://localhost:5003/alert")
    print("  • Ingest: POST http://localhost:5003/ingest")
    print("=" * 50)

    uvicorn.run(app, host="0.0.0.0", port=5003, log_level="info")
