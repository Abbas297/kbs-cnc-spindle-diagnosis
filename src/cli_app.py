"""
Command-Line Interface (CLI) for CNC Spindle & Process Fault Diagnosis KBS
Course: Knowledge-Based Systems (CT-359) — Complex Computing Problem (CCP)
NED University of Engineering & Technology
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inference_engine import (
    KnowledgeBase,
    diagnose,
    diagnose_telemetry,
    get_default_kb_path
)


def display_results(result):
    print("\n" + "=" * 60)
    print("                  DIAGNOSIS RESULTS")
    print("=" * 60)

    # Faults
    print("\n--- Concluded Faults ---")
    if result["faults"]:
        for f, cf in sorted(result["faults"].items(), key=lambda x: -x[1]):
            print(f"  • {f.replace('_', ' ').upper():<28} (Certainty CF: {cf:.2f})")
    else:
        print("  • None (Nominal machine operation)")

    # Safety Warnings
    if result["safety"]:
        print("\n*** CRITICAL SAFETY ALERTS ***")
        for m in result["safety"]:
            print(f"  [!] {m}")

    # Actions
    print("\n--- Recommended Maintenance Actions (Ranked by Safety Priority) ---")
    if result["actions"]:
        for a in result["actions"]:
            print(f"  [{a['id']}] {a['name']}")
            print(f"       Priority: {a['priority']} | Cost: {a['cost']:<8} | Downtime: {a['downtime']:<12} | Who: {a['who']}")
            print(f"       Certainty Factor: {a['cf']:.2f}")
    else:
        print("  • No maintenance intervention required.")

    # Explanation Audit Trail
    print("\n--- Explanation Facility (Audit Trail) ---")
    for e in result["explanations"]:
        print(f"  • {e}")
    print("=" * 60 + "\n")


def menu_symptoms(kb):
    print("\n" + "-" * 50)
    print("  OPERATOR SYMPTOM CHECKLIST")
    print("-" * 50)
    heuristic_symptoms = [
        "unusual_noise",
        "high_vibration",
        "spindle_overheating",
        "poor_surface_finish",
        "increased_power_consumption",
        "metal_particles_in_oil"
    ]
    for i, s in enumerate(heuristic_symptoms, 1):
        print(f"  {i}. {s.replace('_', ' ').title()}")

    print("\nEnter symptom numbers separated by spaces (e.g. 1 2) or 'b' to go back:")
    raw = input("Symptoms > ").strip()
    if raw.lower() in ("b", "back", "q"):
        return

    selected = []
    for token in raw.replace(",", " ").split():
        if token.isdigit():
            idx = int(token) - 1
            if 0 <= idx < len(heuristic_symptoms):
                selected.append(heuristic_symptoms[idx])
        elif token in heuristic_symptoms:
            selected.append(token)

    if not selected:
        print("No valid symptoms selected.")
        return

    print(f"\nEvaluating symptoms: {', '.join(selected)}")
    res = diagnose(selected)
    display_results(res)


def menu_telemetry():
    print("\n" + "-" * 50)
    print("  CNC SENSOR TELEMETRY INPUT (AI4I 2020 STANDARD)")
    print("-" * 50)
    try:
        air_t = float(input("Air Temperature [K] (e.g. 298.1): ") or "298.1")
        proc_t = float(input("Process Temperature [K] (e.g. 308.6): ") or "308.6")
        speed = float(input("Spindle Rotational Speed [rpm] (e.g. 1500): ") or "1500")
        torque = float(input("Spindle Torque [Nm] (e.g. 42.0): ") or "42.0")
        tool_w = float(input("Tool Wear [min] (e.g. 5.0): ") or "5.0")
        ptype = input("Product Variant (L, M, H) [M]: ").strip().upper() or "M"
    except ValueError:
        print("Invalid numerical input. Returning to menu.")
        return

    res = diagnose_telemetry(air_t, proc_t, speed, torque, tool_w, ptype)
    m = res.get("telemetry_metrics", {})
    print("\n--- Physical Calculations ---")
    print(f"  Delta T: {m.get('delta_T_K')} K (HDF threshold: < 8.6 K at speed < 1380 rpm)")
    print(f"  Power:   {m.get('power_watts')} W (PWF threshold: < 3500 W or > 9000 W)")
    print(f"  Overstrain: {m.get('overstrain_min_Nm')} min*Nm (OSF limit for Type {ptype}: {m.get('overstrain_limit')} min*Nm)")
    display_results(res)


def menu_benchmark():
    print("\n" + "-" * 50)
    print("  AI4I 2020 BENCHMARK PRESET DEMOS")
    print("-" * 50)
    demos = [
        ("Nominal Normal Cycle", 298.1, 308.6, 1551.0, 42.8, 5.0, "M"),
        ("Heat Dissipation Failure (HDF)", 298.9, 306.0, 1350.0, 45.0, 30.0, "M"),
        ("Power Failure (PWF Surge)", 298.0, 308.0, 2800.0, 65.0, 25.0, "L"),
        ("Overstrain Failure (OSF)", 298.3, 308.5, 1450.0, 58.0, 215.0, "L"),
        ("Critical Tool Wear (TWF)", 298.4, 308.7, 1520.0, 38.0, 225.0, "M")
    ]
    for i, (name, a, p, s, t, w, ty) in enumerate(demos, 1):
        print(f"  {i}. {name}")

    c = input("\nSelect demo number (1-5) or 'b' to go back: ").strip()
    if c.isdigit() and 1 <= int(c) <= len(demos):
        name, a, p, s, t, w, ty = demos[int(c) - 1]
        print(f"\nRunning Preset: {name}")
        res = diagnose_telemetry(a, p, s, t, w, ty)
        display_results(res)


def menu_batch_validation():
    print("\nRunning full 10,000-row AI4I 2020 validation...")
    import tests.validate_ai4i_dataset as val
    val.main()


def main():
    rules_path = get_default_kb_path()
    kb = KnowledgeBase(rules_path)

    while True:
        print("=" * 65)
        print("   Intelligent KBS for CNC Spindle & Process Fault Diagnosis")
        print("   Course: Knowledge-Based Systems (CT-359) | NED University")
        print("=" * 65)
        print("  1. Operator Heuristic Symptoms Diagnosis")
        print("  2. Process Sensor Telemetry Diagnosis (Manual Input)")
        print("  3. Run Benchmark Presets (HDF, PWF, OSF, Normal)")
        print("  4. Run Full Batch Validation on AI4I 2020 Dataset (10,000 rows)")
        print("  5. Exit")
        print("=" * 65)

        choice = input("Enter choice (1-5): ").strip()
        if choice == "1":
            menu_symptoms(kb)
        elif choice == "2":
            menu_telemetry()
        elif choice == "3":
            menu_benchmark()
        elif choice == "4":
            menu_batch_validation()
        elif choice in ("5", "q", "quit", "exit"):
            print("Exiting KBS. Goodbye!")
            break
        else:
            print("Invalid choice. Try again.\n")


if __name__ == "__main__":
    main()
