"""
Unit and scenario test suite for CNC Spindle & Process Fault Diagnosis KBS
Course: Knowledge-Based Systems (CT-359)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from inference_engine import diagnose, diagnose_telemetry


def test_bearing_wear():
    r = diagnose(["unusual_noise", "high_vibration"])
    assert "bearing_wear" in r["faults"], "Should detect bearing_wear"
    assert any(a["id"] == "A1" for a in r["actions"]), "Should recommend A1"
    print("[OK] Passed: Bearing wear scenario")


def test_bearing_seizure_safety():
    r = diagnose(["spindle_overheating", "high_vibration", "unusual_noise"])
    assert "bearing_seizure" in r["faults"], "Should detect bearing_seizure"
    assert len(r["safety"]) > 0, "Safety alert must be triggered"
    assert "STOP" in r["safety"][0] or "EMERGENCY" in r["safety"][0]
    print("[OK] Passed: Bearing seizure + safety alarm scenario")


def test_contamination():
    r = diagnose(["metal_particles_in_oil", "high_vibration"])
    assert "contamination" in r["faults"], "Should detect contamination"
    assert any(a["id"] == "A3" for a in r["actions"]), "Should recommend A3 oil flush"
    print("[OK] Passed: Lubrication contamination scenario")


def test_bearing_misalignment():
    r = diagnose(["poor_surface_finish", "high_vibration"])
    assert "bearing_misalignment" in r["faults"], "Should detect bearing_misalignment"
    assert any(a["id"] == "A4" for a in r["actions"]), "Should recommend A4 alignment check"
    print("[OK] Passed: Bearing misalignment scenario")


def test_telemetry_hdf():
    # delta_T = 306.0 - 298.5 = 7.5 K (< 8.6 K) and speed = 1350 rpm (< 1380 rpm)
    r = diagnose_telemetry(
        air_temp_k=298.5,
        process_temp_k=306.0,
        speed_rpm=1350,
        torque_nm=42.0,
        tool_wear_min=10,
        product_type="M"
    )
    assert "heat_dissipation_failure" in r["faults"], "Should detect HDF"
    assert any(a["id"] == "A8" for a in r["actions"]), "Should recommend A8 coolant service"
    print("[OK] Passed: Telemetry Heat Dissipation Failure (HDF)")


def test_telemetry_pwf_high():
    # Power = torque * omega. torque=65 Nm, speed=2800 rpm -> P = 65 * 2800 * 2pi/60 = 19058 W (> 9000 W)
    r = diagnose_telemetry(
        air_temp_k=298.0,
        process_temp_k=308.0,
        speed_rpm=2800,
        torque_nm=65.0,
        tool_wear_min=20,
        product_type="L"
    )
    assert "power_failure" in r["faults"], "Should detect PWF"
    assert any(a["id"] == "A7" for a in r["actions"]), "Should recommend A7 drive motor inspection"
    assert len(r["safety"]) > 0, "Should generate electrical safety alert"
    print("[OK] Passed: Telemetry Power Failure (PWF high surge)")


def test_telemetry_osf():
    # Type L threshold is 11,000. Tool wear = 220 min, torque = 55 Nm -> 220 * 55 = 12,100 (> 11,000)
    r = diagnose_telemetry(
        air_temp_k=298.0,
        process_temp_k=308.0,
        speed_rpm=1500,
        torque_nm=55.0,
        tool_wear_min=220,
        product_type="L"
    )
    assert "overstrain_failure" in r["faults"], "Should detect OSF"
    assert any(a["id"] == "A6" for a in r["actions"]), "Should recommend A6 tool replacement"
    assert len(r["safety"]) > 0, "Should generate mechanical stress warning"
    print("[OK] Passed: Telemetry Overstrain Failure (OSF)")


def test_conflict_resolution_and_explanation():
    # Multiple faults triggered simultaneously
    r = diagnose(["unusual_noise", "high_vibration", "spindle_overheating", "metal_particles_in_oil"])
    # Actions should be ranked priority 1 first
    assert r["actions"][0]["priority"] == 1, "Top recommended action must have priority 1"
    assert len(r["explanations"]) >= 4, "Explanation trace must document every fired rule"
    print("[OK] Passed: Conflict resolution ranking and explanation audit facility")


if __name__ == "__main__":
    print("Running KBS Unit Test Suite...")
    test_bearing_wear()
    test_bearing_seizure_safety()
    test_contamination()
    test_bearing_misalignment()
    test_telemetry_hdf()
    test_telemetry_pwf_high()
    test_telemetry_osf()
    test_conflict_resolution_and_explanation()
    print("\nAll 8 KBS unit & scenario tests successfully passed!")
