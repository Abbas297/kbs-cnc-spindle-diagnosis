# Intelligent Knowledge-Based System for CNC Spindle & Process Fault Diagnosis

**Course:** Knowledge-Based Systems (CT-359)  
**Complex Computing Problem (CCP)**  
**Department of Computer Science & Information Technology**  
**NED University of Engineering & Technology, Karachi**

---

## 1. Executive Summary

This project implements an intelligent, rule-based Knowledge-Based System (KBS) for fault diagnosis and maintenance decision support in CNC Vertical Machining Centers. The system addresses industrial equipment diagnostics by integrating two complementary knowledge modules:

1. **Real-Time Sensor Telemetry Diagnosis (Module A):** Formulated from thermodynamic and mechanical physics principles and validated against the benchmark **AI4I 2020 Predictive Maintenance Dataset** (Stephan Matzka, IEEE AI4I 2020; 10,000 operational records). Evaluates air/process temperatures, spindle speed, cutting torque, tool wear, and product quality variants to detect:
   - **Heat Dissipation Failure (HDF):** Low rotational speed combined with inadequate thermal dissipation ($\Delta T < 8.6\text{ K}$, $N < 1380\text{ rpm}$).
   - **Power Failure (PWF):** Drive motor stall or extreme power surges ($P < 3500\text{ W}$ or $P > 9000\text{ W}$).
   - **Overstrain Failure (OSF):** Mechanical overload exceeded for variant thresholds ($\text{Tool wear} \times \tau > 11{,}000 / 12{,}000 / 13{,}000\text{ min}\cdot\text{Nm}$).
   - **Tool Wear Failure (TWF):** Critical tool degradation window ($t \ge 200\text{ min}$).
   - **Random Hardware Failure (RNF):** Stochastic transient anomalies.

2. **Operator Heuristic Symptom Diagnosis (Module B):** Encodes expert mechanical maintenance heuristic rules for spindle rolling element bearings:
   - `bearing_wear`, `bearing_seizure`, `lack_of_lubrication`, `contamination`, and `bearing_misalignment`.

---

## 2. KBS Architecture & Reasoning Engine

- **Knowledge Representation:** Production rules with Certainty Factors (MYCIN-style evidence combination: $CF_{\text{comb}} = CF_1 + CF_2 \times (1 - CF_1)$).
- **Inference Mechanism:** Forward Chaining over working memory.
- **Conflict Resolution Strategy:**
  1. *Safety Priority:* Immediate emergency alarms and machine halts fire first.
  2. *Maintenance Action Priority:* Priority 1 (immediate repair) before Priority 2/3.
  3. *Certainty Factor:* Higher confidence actions prioritized.
  4. *Cost & Downtime:* Lower downtime/cost preferred among equal priorities.
- **Explanation Facility:** Full audit trail detailing why each rule fired, the triggering conditions, and confidence levels.

---

## 3. Project Directory Structure

```
kbs_cnc_project/
├── knowledge_base/
│   ├── rules.json              # Unified production rule base (25 rules, 11 symptoms, 10 faults, 9 actions)
│   └── ai4i2020.csv            # 10,000-row AI4I 2020 Predictive Maintenance Dataset (IEEE AI4I 2020)
├── src/
│   ├── inference_engine.py     # Core inference engine (Forward Chaining + CF + telemetry processing)
│   ├── gui_app.py              # Desktop GUI (Tkinter — zero external dependencies)
│   ├── cli_app.py              # Interactive console CLI application
│   └── streamlit_app.py        # Modern Web GUI (Streamlit)
├── tests/
│   ├── test_cases.py           # Unit and scenario test suite (8 tests)
│   └── validate_ai4i_dataset.py# Batch validation on 10,000 rows (confusion matrices & metrics)
├── docs/                       # Project documentation & reference assets
└── README.md                   # Complete system documentation
```

---

## 4. How to Run the Applications

### Option A: Desktop GUI (Recommended — Built into Python Tkinter)
No external libraries needed. Run directly:
```bash
cd kbs_cnc_project
python src/gui_app.py
```
*Features:* Dual tabs for **Sensor Telemetry Diagnosis** and **Operator Heuristic Checklist**, quick 1-click benchmark scenario presets, and real-time explanation boxes.

### Option B: Interactive Command-Line Interface (CLI)
```bash
cd kbs_cnc_project
python src/cli_app.py
```
*Features:* Interactive menu to evaluate symptoms, enter telemetry values, test presets, or run full batch validation.

### Option C: Modern Streamlit Web Application
```bash
cd kbs_cnc_project
streamlit run src/streamlit_app.py
```
*Features:* Interactive sliders, live power and $\Delta T$ metric gauges, scenario selector, and interactive 10,000-row batch evaluation table.

---

## 5. Verification & Validation Testing

### 1. Full 10,000-Row AI4I 2020 Dataset Benchmark
Run the batch validator over all 10,000 records:
```bash
python tests/validate_ai4i_dataset.py
```
**Results on 10,000 Cycles:**
- **Heat Dissipation Failure (HDF):** 100.00% Accuracy, 100.00% Precision, 100.00% Recall ($F_1 = 1.0000$)
- **Power Failure (PWF):** 100.00% Accuracy, 100.00% Precision, 100.00% Recall ($F_1 = 1.0000$)
- **Overstrain Failure (OSF):** 100.00% Accuracy, 100.00% Precision, 100.00% Recall ($F_1 = 1.0000$)
- **Overall Deterministic Machine Failure:** **99.48% Accuracy**, **100.00% Precision** (0 False Alarms across 9,661 normal operating cycles).

### 2. Automated Unit & Scenario Tests
```bash
python tests/test_cases.py
```
Verifies all 8 functional test suites covering bearing wear, seizure safety alarms, contamination, misalignment, telemetry HDF, PWF, OSF, and conflict resolution ranking.

---

## 6. Sample Test Cases

| Scenario / Inputs | Mode | Expected Fault | Primary Recommended Action | Safety Alert? |
|---|---|---|---|---|
| `unusual_noise` + `high_vibration` | Symptom | `bearing_wear` (CF=0.80) | `A1`: Replace spindle bearings | No |
| `spindle_overheating` + `high_vibration` + `unusual_noise` | Symptom | `bearing_seizure` (CF=0.95) | `A1`: Replace spindle bearings | **YES: EMERGENCY STOP** |
| `metal_particles_in_oil` + `high_vibration` | Symptom | `contamination` (CF=0.85) | `A3`: Flush lubrication & change oil | No |
| `poor_surface_finish` + `high_vibration` | Symptom | `bearing_misalignment` (CF=0.70) | `A4`: Check & correct alignment | No |
| Air=298.9 K, Proc=306.0 K ($\Delta T=7.1\text{ K}$), Speed=1350 rpm | Telemetry | `heat_dissipation_failure` (CF=0.98) | `A8`: Service heat exchanger & cooling jacket | No |
| Speed=2800 rpm, Torque=65 Nm ($P=19{,}058\text{ W} > 9000\text{ W}$) | Telemetry | `power_failure` (CF=0.99) | `A7`: Inspect spindle motor & VFD | **YES: Drive Anomaly** |
| Tool Wear=220 min, Torque=55 Nm, Type L ($S=12{,}100 > 11{,}000$) | Telemetry | `overstrain_failure` (CF=0.99) | `A6`: Replace cutting tool + `A9`: De-rate feed | **YES: Mechanical Stress** |

---

## 7. Programmatic Python API

```python
from src.inference_engine import diagnose, diagnose_telemetry

# 1. Symptom Diagnosis
result = diagnose(["unusual_noise", "high_vibration", "spindle_overheating"])
print("Faults:", result["diagnosed_faults"])
print("Actions:", [a["name"] for a in result["recommended_actions"]])
if result["safety_alerts"]:
    print("Safety Warning:", result["safety_alerts"])

# 2. Telemetry Diagnosis (AI4I 2020 Data)
tel_result = diagnose_telemetry(
    air_temp_k=298.9,
    process_temp_k=306.0,
    speed_rpm=1350,
    torque_nm=45.0,
    tool_wear_min=30,
    product_type="M"
)
print("Telemetry Faults:", tel_result["faults"])
print("Explanations:\n", tel_result["explanation_text"])
```

---

## 8. Academic References

1. **Matzka, S. (2020)**. *Explainable Artificial Intelligence for Predictive Maintenance Applications*. Third International Conference on Artificial Intelligence for Industries (AI4I 2020), IEEE, pp. 69–74. DOI: `10.1109/AI4I49448.2020.00023`.
2. **Giarratano, J. C., & Riley, G. (2005)**. *Expert Systems: Principles and Programming* (4th ed.). Course Technology / Thomson Learning.
3. **ISO 10816-3 (2009)**. *Mechanical vibration — Evaluation of machine vibration by measurements on non-rotating parts*. International Organization for Standardization.
4. **Shortliffe, E. H., & Buchanan, B. G. (1975)**. *A model of inexact reasoning in medicine*. Mathematical Biosciences, 23(3-4), 351-379.
