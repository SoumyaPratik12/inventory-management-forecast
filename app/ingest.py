import csv
from datetime import datetime
from models import get_session, Inventory, Sales, create_tables


def ingest_csvs():
    create_tables()
    session = get_session()

    try:
        # Load inventory CSV
        with open("../data/inventory.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                inventory = Inventory(
                    sku=row['sku'], unit_cost=float(
                        row['unit_cost']), quantity_on_hand=int(
                        row['quantity_on_hand']), expiry_date=datetime.strptime(
                        row['expiry_date'], '%Y-%m-%d').date())
                session.merge(inventory)

        # Load sales CSV
        with open("../data/sales.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sales = Sales(
                    sku=row['sku'],
                    units_sold=int(row['units_sold']),
                    date=datetime.strptime(row['date'], '%Y-%m-%d').date()
                )
                session.add(sales)

        session.commit()
        print("CSVs loaded successfully")

    except Exception as e:
        session.rollback()
        print(f"Error loading CSVs: {e}")
        raise
    finally:
        session.close()
