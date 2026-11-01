"""
Data Generator — Smart Waste Management Platform (Greater Noida, India)
Generates 365 days of realistic synthetic fill-level history for 120 smart bins
distributed across Greater Noida's sectors.

Bin count: 120
City: Greater Noida, Uttar Pradesh, India
Data points: 100 bins × 365 days × 24 hrs = 876,000 records
Trucks: 5 municipal collection trucks

Hardware Note:
    These bins mirror the data schema that an actual ESP32+Ultrasonic Sensor
    would transmit. Each record = one hourly IoT reading.

Run:
    python -m ml.data_generator.generator
"""
import os
import sys
import datetime
import random
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

# Allow imports from project root
# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from database.db import engine, init_db, SessionLocal
from database.models import Bin, FillHistory, Truck, Driver
from ml.preprocessing.calendar_features import GREATER_NOIDA_HOLIDAYS

# ──────────────────────────────────────────────────────────────
#  120 Greater Noida BINS — Real GPS Coordinates
#  Spread across wards, landmarks, and neighbourhoods
# ──────────────────────────────────────────────────────────────

GREATER_NOIDA_BINS = [
    # ── Route 1: Alpha Sectors (Alpha I, Alpha II) ──
    {"bin_id":"GN-ALPHA1-001","lat":28.4715,"lon":77.5121,"street":"Alpha I Main Road","area":"Alpha I Sector","ward":"Alpha","ward_num":1,"area_type":"Residential","cap":240},
    {"bin_id":"GN-ALPHA1-002","lat":28.4720,"lon":77.5105,"street":"Alpha I Commercial Belt","area":"Alpha I Sector","ward":"Alpha","ward_num":1,"area_type":"Commercial","cap":360},
    {"bin_id":"GN-ALPHA1-003","lat":28.4731,"lon":77.5112,"street":"Alpha I Park Area","area":"Alpha I Sector","ward":"Alpha","ward_num":1,"area_type":"Park","cap":180},
    {"bin_id":"GN-ALPHA1-004","lat":28.4742,"lon":77.5089,"street":"Alpha I Market","area":"Alpha I Sector","ward":"Alpha","ward_num":1,"area_type":"Market","cap":480},
    {"bin_id":"GN-ALPHA1-005","lat":28.4750,"lon":77.5075,"street":"Alpha I Metro Pillar","area":"Alpha I Sector","ward":"Alpha","ward_num":1,"area_type":"Residential","cap":240},
    {"bin_id":"GN-ALPHA2-001","lat":28.4781,"lon":77.5140,"street":"Alpha II Sector Road","area":"Alpha II Sector","ward":"Alpha","ward_num":1,"area_type":"Residential","cap":240},
    # ── Route 2: Beta Sectors (Beta I, Beta II) ──
    {"bin_id":"GN-BETA1-001","lat":28.4812,"lon":77.5165,"street":"Beta I Main Road","area":"Beta I Sector","ward":"Beta","ward_num":2,"area_type":"Residential","cap":240},
    {"bin_id":"GN-BETA2-011","lat":28.4855,"lon":77.5201,"street":"Beta II Market","area":"Beta II Sector","ward":"Beta","ward_num":2,"area_type":"Market","cap":420},
    # ── Route 3: Gamma Sectors (Gamma I, Gamma II) ──
    {"bin_id":"GN-GAMMA1-007","lat":28.4901,"lon":77.5245,"street":"Gamma I Shopping Complex","area":"Gamma I Sector","ward":"Gamma","ward_num":3,"area_type":"Commercial","cap":360},
    {"bin_id":"GN-GAMMA2-001","lat":28.4925,"lon":77.5260,"street":"Gamma II Residential","area":"Gamma II Sector","ward":"Gamma","ward_num":3,"area_type":"Residential","cap":240},
    # ── Route 4: Delta Sectors (Delta I, Delta II) ──
    {"bin_id":"GN-DELTA1-003","lat":28.4950,"lon":77.5301,"street":"Delta I Central Park","area":"Delta I Sector","ward":"Delta","ward_num":4,"area_type":"Park","cap":180},
    {"bin_id":"GN-DELTA1-015","lat":28.4965,"lon":77.5310,"street":"Delta I Market Lane","area":"Delta I Sector","ward":"Delta","ward_num":4,"area_type":"Market","cap":420},
    {"bin_id":"GN-DELTA2-001","lat":28.4981,"lon":77.5335,"street":"Delta II Residential Gate","area":"Delta II Sector","ward":"Delta","ward_num":4,"area_type":"Residential","cap":240},
    # ── Route 5: Knowledge Park (III) & Yamuna Expressway ──
    {"bin_id":"GN-KP3-001","lat":28.4635,"lon":77.4951,"street":"Knowledge Park III Institutional Area","area":"Knowledge Park (III)","ward":"KP","ward_num":5,"area_type":"School","cap":500},
    {"bin_id":"GN-KP3-002","lat":28.4650,"lon":77.4930,"street":"Knowledge Park Block B","area":"Knowledge Park (III)","ward":"KP","ward_num":5,"area_type":"School","cap":480},
    {"bin_id":"GN-YAMUNA-001","lat":28.4501,"lon":77.5401,"street":"Yamuna Expressway Service Road","area":"Yamuna Expressway","ward":"Highway","ward_num":6,"area_type":"Commercial","cap":500},

]
# ─────────────────────────────────────────────────────────────
#  TRUCK FLEET (Municipal Corporation of Hyderabad)
# ─────────────────────────────────────────────────────────────

TRUCK_FLEET = [
    {"truck_id": "GN-01", "plate": "UP16EA0001", "capacity": 5000, "driver": "Amit Singh", "driver_id": "DRV001"},
    {"truck_id": "GN-02", "plate": "UP16EA0002", "capacity": 5000, "driver": "Rahul Sharma", "driver_id": "DRV002"},
    {"truck_id": "GN-03", "plate": "UP16EA0003", "capacity": 5000, "driver": "Vikas Yadav", "driver_id": "DRV003"},
    {"truck_id": "GN-04", "plate": "UP16EA0004", "capacity": 5000, "driver": "Sunil Kumar", "driver_id": "DRV004"},
    {"truck_id": "GN-05", "plate": "UP16EA0005", "capacity": 4000, "driver": "Pankaj Chaudhary", "driver_id": "DRV005"},
]

DRIVER_DETAILS = [
    {"driver_id":"DRV001","name":"Ramesh Kumar","phone":"9876543210","license":"UP123456"},
    {"driver_id":"DRV002","name":"Suresh","phone":"9876543211","license":"UP123457"},
    {"driver_id":"DRV003","name":"Vijay Babu",  "phone":"9876543212","license":"UP123458"},
    {"driver_id":"DRV004","name":"Naresh Yadav","phone":"9876543213","license":"UP123459"},
    {"driver_id":"DRV005","name":"Prasad Goud", "phone":"9876543214","license":"UP123460"},
]

# ─────────────────────────────────────────────────────────────
#  AREA PARAMETERS
# ─────────────────────────────────────────────────────────────

AREA_PARAMS = {
    "Residential":      {"base_fill_rate": 1.8,  "peak_hours": [7, 8, 12, 18, 19, 20], "pop_density": 4500, "holiday_boost": 1.2},
    "Commercial":       {"base_fill_rate": 2.5,  "peak_hours": [9, 10, 11, 12, 13, 14, 15, 16], "pop_density": 8000, "holiday_boost": 0.4},
    "Market":           {"base_fill_rate": 3.8,  "peak_hours": [8, 9, 10, 11, 12, 16, 17, 18, 19], "pop_density": 12000, "holiday_boost": 1.6},
    "Hospital":         {"base_fill_rate": 2.2,  "peak_hours": [8, 9, 10, 11, 14, 15, 16], "pop_density": 5000, "holiday_boost": 0.8},
    "School":           {"base_fill_rate": 2.0,  "peak_hours": [7, 8, 12, 13, 16, 17], "pop_density": 3500, "holiday_boost": 0.1},
    "Restaurant":       {"base_fill_rate": 3.2,  "peak_hours": [11, 12, 13, 19, 20, 21], "pop_density": 6000, "holiday_boost": 1.5},
    "Mall":             {"base_fill_rate": 3.5,  "peak_hours": [11, 12, 13, 14, 15, 16, 17, 18, 19, 20], "pop_density": 10000, "holiday_boost": 1.8},
    "Bus Stand":        {"base_fill_rate": 2.8,  "peak_hours": [7, 8, 9, 17, 18, 19], "pop_density": 7000, "holiday_boost": 1.1},
    "Railway Station":  {"base_fill_rate": 3.0,  "peak_hours": [6, 7, 8, 16, 17, 18, 19], "pop_density": 9000, "holiday_boost": 1.3},
    "Park":             {"base_fill_rate": 0.9,  "peak_hours": [6, 7, 17, 18, 19], "pop_density": 2000, "holiday_boost": 1.7},
    "Industrial":       {"base_fill_rate": 2.0,  "peak_hours": [8, 9, 10, 14, 15, 16], "pop_density": 3000, "holiday_boost": 0.2},
}

from ml.preprocessing.calendar_features import GREATER_NOIDA_HOLIDAYS

# Monsoon months in Hyderabad: June–October (higher rainfall, affects bin usage)
MONSOON_MONTHS = {6, 7, 8, 9, 10}


def generate_hourly_fill(bin_data, timestamp, current_fill, is_holiday, temperature, rainfall):
    """
    Simulates fill percentage increase for one hour, given bin context.
    Returns (new_fill, waste_generated).
    """
    params = AREA_PARAMS[bin_data["area_type"]]
    hour = timestamp.hour
    
    base_rate = params["base_fill_rate"]
    
    # Peak hour multiplier
    hour_multiplier = 1.8 if hour in params["peak_hours"] else 0.6
    
    # Holiday/weekend multiplier
    is_weekend = timestamp.weekday() >= 5
    if is_holiday:
        day_multiplier = params["holiday_boost"]
    elif is_weekend:
        day_multiplier = 1.1
    else:
        day_multiplier = 1.0
    
    # Temperature effect (higher temp = more waste/spoilage)
    temp_effect = 1.0 + max(0, (temperature - 28) * 0.02)
    
    # Rainfall effect (heavy rain suppresses outdoor activity)
    rain_effect = 1.0 - min(0.4, rainfall * 0.05)
    
    # Random natural variability (±15%)
    noise = np.random.normal(1.0, 0.15)
    
    # Final waste rate as percentage of capacity per hour
    capacity_liters = bin_data["cap"]
    fill_rate = (base_rate * hour_multiplier * day_multiplier * temp_effect * rain_effect * noise)
    waste_liters = fill_rate * (capacity_liters / 100.0)
    waste_liters = max(0, waste_liters)
    
    # Add waste to fill
    new_fill_liters = (current_fill / 100.0) * capacity_liters + waste_liters
    new_fill_pct = min(100.0, (new_fill_liters / capacity_liters) * 100.0)
    
    return new_fill_pct, waste_liters


def run_generation():
    """
    Main data generation pipeline.
    """
    print("=" * 60)
    print("  SMART WASTE MANAGEMENT - DATA GENERATOR")
    print("  City: Greater Noida, Uttar Pradesh, India")
    print(f"  Bins: {len(GREATER_NOIDA_BINS)}")
    print("=" * 60)
    
    init_db()
    db: Session = SessionLocal()
    
    try:
        # ── Clear existing data ──
        print("\n[1/5] Clearing existing data...")
        db.query(FillHistory).delete()
        db.query(Bin).delete()
        db.query(Truck).delete()
        db.query(Driver).delete()
        db.commit()
        
        # ── Insert Drivers ──
        print("[2/5] Inserting driver records...")
        for d in DRIVER_DETAILS:
            driver = Driver(
                driver_id=d["driver_id"],
                name=d["name"],
                phone=d["phone"],
                license_number=d["license"],
                status="Available"
            )
            db.add(driver)
        db.commit()
        
        # ── Insert Bins ──
        print("[3/5] Inserting 100 Greater Noida bin records...")
        installation_base = datetime.date(2022, 1, 1)
        for i, b in enumerate(GREATER_NOIDA_BINS):
            install_date = installation_base + datetime.timedelta(days=random.randint(0, 180))
            bin_obj = Bin(
                bin_id=b["bin_id"],
                latitude=b["lat"],
                longitude=b["lon"],
                street_name=b["street"],
                area_name=b["area"],
                ward=b["ward"],
                ward_number=b["ward_num"],
                area_type=b["area_type"],
                capacity=b["cap"],
                current_fill_percentage=random.uniform(10, 60),
                battery_level=random.uniform(75, 100),
                signal_strength=random.randint(65, 98),
                temperature=None,
                status="Active",
                last_updated=None,
                last_collection_time=None,
                installation_date=install_date
            )
            db.add(bin_obj)
        db.commit()
        print(f"  [OK] Inserted {len(GREATER_NOIDA_BINS)} bins")

        # ── Insert Trucks ──
        print("[4/5] Inserting truck fleet...")
        for t in TRUCK_FLEET:
            truck = Truck(
                truck_id=t["truck_id"],
                plate_number=t["plate"],
                capacity=t["capacity"],
                driver=t["driver"],
                driver_id=t["driver_id"],
                status="Idle"
            )
            db.add(truck)
        db.commit()
        print(f"  [OK] Inserted {len(TRUCK_FLEET)} trucks")
        
        # ── Generate Historical Fill Data ──
        print("[5/5] Generating 365 days of hourly fill history...")
        
        # Start date: 365 days ago
        start_dt = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - datetime.timedelta(days=365)
        
        BATCH_SIZE = 5000
        records_buffer = []
        total_records = 0
        
        # Track current fill state per bin
        bin_fill_state = {b["bin_id"]: random.uniform(5, 25) for b in GREATER_NOIDA_BINS}
        
        # Simulate collection events: each bin collected every ~3-5 days randomly
        last_collection = {b["bin_id"]: start_dt for b in GREATER_NOIDA_BINS}
        
        total_hours = 365 * 24
        for h in range(total_hours):
            current_dt = start_dt + datetime.timedelta(hours=h)
            date_str = current_dt.strftime("%Y-%m-%d")
            is_holiday = date_str in GREATER_NOIDA_HOLIDAYS
            month = current_dt.month
            
            # Greater Noida climate simulation
            base_temp = 28 + 6 * np.sin(np.pi * (month - 3) / 6)  # Peak in May, low in Jan
            temperature = float(np.clip(np.random.normal(base_temp, 2.5), 18, 45))
            
            # Rainfall (monsoon: June–Oct)
            if month in MONSOON_MONTHS:
                rainfall = float(max(0, np.random.exponential(8)))
            else:
                rainfall = float(max(0, np.random.exponential(0.5)))
            
            for b in GREATER_NOIDA_BINS:
                bin_id = b["bin_id"]
                current_fill = bin_fill_state[bin_id]
                
                # Simulate collection: if fill > 85% or > 4 days since last collection
                hours_since = (current_dt - last_collection[bin_id]).total_seconds() / 3600
                should_collect = (current_fill >= 85.0) or (hours_since >= random.randint(72, 120))
                if should_collect and current_fill > 20:
                    current_fill = random.uniform(2, 10)  # Reset after collection
                    last_collection[bin_id] = current_dt
                
                # Generate new fill
                new_fill, waste_gen = generate_hourly_fill(b, current_dt, current_fill, is_holiday, temperature, rainfall)
                bin_fill_state[bin_id] = new_fill
                
                pop_density = AREA_PARAMS[b["area_type"]]["pop_density"]
                
                records_buffer.append({
                    "bin_id": bin_id,
                    "timestamp": current_dt,
                    "fill_percentage": round(new_fill, 2),
                    "battery": round(random.uniform(75, 100), 1),
                    "temperature": round(temperature, 1),
                    "rainfall": round(rainfall, 2),
                    "holiday": int(is_holiday),
                    "population_density": pop_density,
                    "waste_generated": round(waste_gen, 2),
                })
            
            # Batch insert
            if len(records_buffer) >= BATCH_SIZE:
                db.bulk_insert_mappings(FillHistory, records_buffer)
                db.commit()
                total_records += len(records_buffer)
                records_buffer = []
                pct = (h / total_hours) * 100
                print(f"  Progress: {pct:.0f}% — {total_records:,} records written", end="\r")
        
        # Insert remaining
        if records_buffer:
            db.bulk_insert_mappings(FillHistory, records_buffer)
            db.commit()
            total_records += len(records_buffer)
        
        print(f"\n  [OK] Inserted {total_records:,} fill history records")
        print("\n" + "=" * 60)
        print("  DATA GENERATION COMPLETE!")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Data generation failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_generation()
