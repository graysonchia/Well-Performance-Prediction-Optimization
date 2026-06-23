"""
Example client script for calling ML prediction endpoints.
Run this after starting the backend API.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1/predictions"


def demo_forecasting():
    """Demo: Production Forecasting"""
    print("\n" + "="*60)
    print("DEMO: PRODUCTION FORECASTING")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/well/1/forecast",
            params={"days_ahead": 30}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Well: {data['well_name']}")
            print(f"  Forecasting next {data['forecast_days']} days\n")
            
            for item in data['forecast'][:7]:  # Show first week
                print(f"  {item['date']}: {item['predicted_oil_bbl']:.1f} BBL")
            print(f"  ... and {len(data['forecast'])-7} more days")
        else:
            print(f"✗ Error: {response.json()['detail']}")
    except Exception as e:
        print(f"✗ Connection failed: {e}")


def demo_anomalies():
    """Demo: Anomaly Detection"""
    print("\n" + "="*60)
    print("DEMO: ANOMALY DETECTION")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/well/1/anomalies")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Well: {data['well_name']}")
            print(f"  Total readings: {data['total_readings']}")
            print(f"  Anomalies detected: {data['anomalies_detected']}\n")
            
            if data['anomalies']:
                for anom in data['anomalies'][:3]:
                    print(f"  Reading {anom['index']} - Score: {anom['anomaly_score']:.3f}")
                    print(f"    Temperature: {anom['reading'].get('temperature_c')}°C")
                    print(f"    Vibration: {anom['reading'].get('vibration_mms')} mm/s\n")
            else:
                print("  No anomalies detected ✓")
        else:
            print(f"✗ Error: {response.json()['detail']}")
    except Exception as e:
        print(f"✗ Connection failed: {e}")


def demo_health():
    """Demo: Well Health & Maintenance"""
    print("\n" + "="*60)
    print("DEMO: WELL HEALTH & MAINTENANCE")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/well/1/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Well: {data['well_name']}")
            print(f"  Health Score: {data['health_score']}/100")
            print(f"  Status: {data['status']}")
            print(f"  Message: {data['message']}")
            
            if data['last_reading']:
                print(f"\n  Last Reading:")
                for key, value in data['last_reading'].items():
                    if isinstance(value, float):
                        print(f"    {key}: {value:.2f}")
        else:
            print(f"✗ Error: {response.json()['detail']}")
    except Exception as e:
        print(f"✗ Connection failed: {e}")


def demo_comprehensive():
    """Demo: Comprehensive Analysis"""
    print("\n" + "="*60)
    print("DEMO: COMPREHENSIVE WELL ANALYSIS")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/well/1/analysis")
        
        if response.status_code == 200:
            data = response.json()
            analysis = data['analysis']
            
            print(f"\n✓ Well: {data['well_name']}")
            print(f"\n  HEALTH:")
            print(f"    Score: {analysis['health_score']:.1f}/100")
            print(f"    Status: {analysis['maintenance_status']}")
            print(f"    Message: {analysis['maintenance_message']}")
            
            print(f"\n  FORECAST:")
            print(f"    Records: {len(analysis['forecast'])}")
            if analysis['forecast']:
                first = analysis['forecast'][0]
                print(f"    Next day: {first['predicted_oil_bbl']:.1f} BBL")
            
            print(f"\n  ANOMALIES:")
            print(f"    Detected: {len(analysis['anomalies'])}")
            
            print(f"\n  Generated: {analysis['timestamp']}")
        else:
            print(f"✗ Error: {response.json()['detail']}")
    except Exception as e:
        print(f"✗ Connection failed: {e}")


def demo_field_analysis():
    """Demo: Field-Level Analysis"""
    print("\n" + "="*60)
    print("DEMO: FIELD-LEVEL ANALYSIS")
    print("="*60)
    
    try:
        # Try common field name, replace with your actual field name
        response = requests.get(f"{BASE_URL}/field/Tembikai/analysis")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Field: {data['field_name']}")
            print(f"  Wells analyzed: {data['wells_analyzed']}\n")
            
            for analysis in data['analyses'][:3]:  # Show first 3 wells
                print(f"  {analysis['well_name']}:")
                print(f"    Health: {analysis['health_score']:.1f}/100")
                print(f"    Status: {analysis['maintenance_status']}")
                print()
        else:
            print(f"✗ Error: {response.json()['detail']}")
    except Exception as e:
        print(f"✗ Connection failed: {e}")


if __name__ == "__main__":
    print("\n🤖 ML PREDICTIONS API CLIENT")
    print("Make sure the backend is running: uvicorn app.main:app --reload")
    
    demo_forecasting()
    demo_anomalies()
    demo_health()
    demo_comprehensive()
    # demo_field_analysis()  # Uncomment to test field-level analysis
    
    print("\n" + "="*60)
    print("✓ Demo complete!")
    print("="*60)
