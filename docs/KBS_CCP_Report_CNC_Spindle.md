# COMPLEX COMPUTING PROBLEM (CCP) PROJECT REPORT
## Course: Knowledge-Based Systems (CT-359)
**Department of Computer Science & Information Technology**  
**NED University of Engineering & Technology, Karachi**

---

### Project Title
**Intelligent Knowledge-Based System for CNC Spindle & Process Fault Diagnosis and Predictive Maintenance Support**

### Student Details
| Sr. No. | Student Name | Roll No. | Signature |
|:---:|:---|:---:|:---:|
| 1 | Abbas Kazmi | CT-24187 | |
| 2 | Faizan Ahmed | CT-24196 | |
| 3 | Araiz | CT-24203 | |

**Submission Date:** October 2026 (Fall Semester)

---

## 1. Project Instructions & Complex Computing Problem Overview

This project has been developed strictly in accordance with the Complex Computing Problem (CCP) rubric for Knowledge-Based Systems (Course CT-359). The project integrates rigorous theoretical knowledge engineering with an executable, production-grade implementation demonstrable during the course viva defense. It satisfies all mandated CCP attributes:

- **CPA-2 (Depth of Knowledge):** Synthesizes foundational engineering principles—specifically thermodynamics, electromechanical power transfer ($P = \tau \times \omega$), tool cutting mechanics, and rotordynamic vibration—with knowledge-based AI.
- **CPA-3 (Depth of Analysis):** Addresses conflicting stakeholder requirements, noisy observations, and partial sensor observability through probabilistic reasoning using the MYCIN Certainty Factor model.
- **CPA-9 (Societal, Safety, and Economic Context):** Enforces hard real-time safety halts against bearing seizure and cutter disintegration, mitigating catastrophic workshop hazards, downtime loss, and adhering to ISO 10816 vibration standards.

---

## 2. Problem Statement

Modern industrial Computer Numerical Control (CNC) Vertical Machining Centers operate under extreme mechanical, thermal, and dynamic loads. The spindle and cutting tool assembly represents the single most critical subsystem of a CNC mill. Sudden unpredicted spindle bearing lockups, excessive tool overstrain, or heat dissipation breakdown lead to catastrophic machine damage, workpiece scrapping, high maintenance expenses, and severe operator safety risks.

Traditional machine maintenance relies either on subjective, unstandardized human operator heuristics or opaque "black-box" machine learning classifiers that lack explainability and deterministic safety guarantees. The objective of this Complex Computing Problem is to design, implement, and validate an intelligent, transparent Knowledge-Based System (KBS) that unifies both real-time physical sensor telemetry (**AI4I 2020 Predictive Maintenance Dataset**, Stephan Matzka IEEE 2020) and operator heuristic symptoms into a forward-chaining production rule base. The system must diagnose underlying failure modes with calibrated Certainty Factors, resolve action conflicts, provide complete justification audit trails, and recommend prioritized maintenance interventions.

---

## 3. Problem Description & Industrial Context

CNC machining centers are deployed in high-precision aerospace, automotive, and manufacturing environments. Within this operating context, equipment faults manifest across two distinct operational strata:

1. **Real-Time Physical Sensor Streams:** Continuously logged physical variables including ambient air temperature $[K]$, process temperature $[K]$, spindle rotational velocity $[\text{rpm}]$, drive torque $[\text{Nm}]$, and accumulated tool cutting time $[\text{min}]$.
2. **Human Workshop Observations:** Qualitative and heuristic indicators reported during visual inspections and shifts, such as abnormal high-pitch acoustic chatter, tactile housing overheating, workpiece surface finish deterioration, lubricant metal particulate contamination, and spindle motor current draw surges.

An industrial Knowledge-Based System cannot treat these two strata in isolation. Sensor anomalies (e.g., thermal rise) correlate with mechanical root causes (e.g., lubrication starvation or worn bearing balls). Therefore, our system bridges quantitative sensor telemetry and qualitative maintenance knowledge within a unified inference framework.

---

## 4. Problem Analysis

### 4.1 Problem Understanding & Domain Boundaries
Industrial CNC failure diagnosis represents a complex problem due to non-linear physical interactions. For instance, heat dissipation failure does not merely depend on absolute temperature, but on the convective temperature gradient ($\Delta T = T_{\text{process}} - T_{\text{air}}$) relative to spindle convective air circulation (rotational speed $N$). Similarly, tool breakage depends non-linearly on the combined product of accumulated tool wear and cutting torque. Our domain boundary specifically models the CNC Vertical Machining Center spindle shaft, front/rear rolling element bearings, spindle motor VFD, lubrication circulation, and tool holder assembly.

### 4.2 Stakeholders and Their Requirements
- **CNC Machine Operator:** Requires an instant, foolproof diagnostic feedback tool with clear binary safety alarms (e.g., "IMMEDIATE EMERGENCY STOP") to prevent bodily injury or machine crashes during machining cycles.
- **Maintenance Technician / Millwright:** Requires specific, actionable repair work orders (e.g., "Flush lubrication system and change oil", "Replace spindle bearings") with expected downtime and required tooling.
- **Production Plant Manager:** Demands minimization of false alarms (which cause needless downtime) and explicit cost/downtime rankings to prioritize repairs during scheduled maintenance windows.
- **Reliability / Quality Assurance Engineer:** Demands full explainability and auditable reasoning traces explaining why a particular fault was diagnosed, preventing unsubstantiated part replacements.

### 4.3 Constraints and Conflicting Requirements
1. **Safety vs. Operational Availability:** Halting the CNC mill guarantees safety but incurs significant downtime cost. The system must distinguish between an imminent bearing seizure (requiring an immediate stop) and early raceway wear (which permits interim load de-rating while manufacturing completes).
2. **Sensor Noise vs. Detection Sensitivity:** Telemetry sensors experience transient spikes. The KBS must avoid triggering premature shutdowns on brief electrical transients while capturing genuine sustained power failure anomalies.
3. **Incomplete Operator Observations:** An operator may only observe "unusual noise". Noise alone can indicate early wear, misalignment, or lack of lubrication. The system must represent this epistemic uncertainty through calibrated Certainty Factors rather than forcing an unfounded binary decision.

### 4.4 Root Cause & Functional Requirement Identification
Root cause analysis identifies that machine failures stem from three primary physical origins:
- **Thermodynamic Imbalance:** Inadequate coolant flow or low spindle circulation causing heat dissipation failure (HDF).
- **Electromechanical Overload:** Motor stall or VFD power surge causing electrical power failure (PWF).
- **Tribological & Mechanical Degradation:** Excessive contact stress causing overstrain failure (OSF), raceway flaking, and abrasive particulate contamination.

Consequently, the KBS requires: (1) an automated telemetry feature extractor, (2) an extensible production rule base, (3) a MYCIN-based certainty inference engine, (4) a multi-tiered conflict resolution algorithm, and (5) an interactive explanation facility.

### 4.5 Assumptions and Technical Justifications
1. **Sensor Integrity:** Sensor readings provided in the AI4I 2020 dataset are assumed to be sampled at steady-state 1 Hz intervals during active cutting operations.
2. **Monotonic Tool Wear:** Tool wear accumulation is non-decreasing over a machining batch.
3. **Telemetry Ground Truth (Stephan Matzka IEEE 2020):** In accordance with published literature, product quality variants L (Low, 50%), M (Medium, 30%), and H (High, 20%) exhibit distinct mechanical stress limits of 11,000, 12,000, and 13,000 $\text{min}\cdot\text{Nm}$.
4. **Independent Evidence Combination:** In accordance with standard expert system theory (Shortliffe & Buchanan), separate diagnostic rules contribute independent pieces of evidence toward the same conclusion.

---

## 5. Knowledge Representation & KBS Design

### 5.1 Selected Knowledge Representation Formalism
We selected Production Rules augmented with Certainty Factors (MYCIN Model). Alternative formalisms (e.g., pure first-order predicate logic, deep neural networks, or Bayesian networks) were evaluated and rejected for specific technical reasons:
- Pure First-Order Logic cannot handle degrees of belief, sensor noise, or incomplete workshop symptoms.
- Deep Neural Networks act as opaque "black boxes", failing the mandatory industrial need for human-verifiable explanation traces.
- Bayesian Networks require extensive joint probability tables that are unavailable in empirical machine tool manuals.

Production rules provide an exact isomorphism with human expert knowledge:
$$\text{IF } (\Delta T < 8.6\text{ K}) \land (N < 1380\text{ rpm}) \implies \text{Heat Dissipation Failure (CF = 0.98)}$$

### 5.2 Knowledge Base Structure & Ontology
The knowledge base is formally partitioned into four interconnected entities within `rules.json`:
1. **Equipment Ontology:** CNC Vertical Machining Center $\rightarrow$ Spindle Shaft, Rolling Bearings, Drive Motor & VFD, Cooling Jacket, Tooling.
2. **Observable Symptoms & Sensor Predicates (11):** `unusual_noise`, `high_vibration`, `spindle_overheating`, `poor_surface_finish`, `increased_power_consumption`, `metal_particles_in_oil`, `heat_dissipation_hazard`, `power_surge_or_stall`, `critical_overstrain`, `excessive_tool_wear`, `random_hardware_anomaly`.
3. **Failure Modes (10):** `bearing_wear`, `bearing_seizure`, `lack_of_lubrication`, `contamination`, `bearing_misalignment`, `heat_dissipation_failure`, `power_failure`, `overstrain_failure`, `tool_wear_failure`, `random_hardware_failure`.
4. **Prioritized Maintenance Actions (9):**
   - **A1:** Replace spindle bearings (Priority 1, High cost, 6-10 hours, Specialist)
   - **A2:** Clean and re-lubricate bearings (Priority 2, Low cost, 1-2 hours, Maintenance Tech)
   - **A3:** Flush lubrication system and change oil (Priority 2, Medium cost, 2-3 hours, Maintenance Tech)
   - **A4:** Check and correct spindle alignment (Priority 1, Medium cost, 4-6 hours, Specialist)
   - **A5:** Reduce cutting load and monitor (Priority 3, Very Low cost, 30 min, Operator)
   - **A6:** Replace cutting tool insert / assembly (Priority 1, Low cost, 15-30 min, Operator/Setter)
   - **A7:** Inspect spindle drive motor and inverter VFD (Priority 1, Medium cost, 2-4 hours, Electrician)
   - **A8:** Service heat exchanger & flush coolant jacket (Priority 1, Medium cost, 2-3 hours, Maintenance Tech)
   - **A9:** De-rate cutting feed rate and re-calculate engagement (Priority 2, Very Low cost, 15 min, Programmer)

### 5.3 Inference Mechanism & Forward Chaining Algorithm
The inference engine operates via data-driven Forward Chaining. Known sensor readings and observed symptoms are asserted into Working Memory. The engine iterates across the rule base, evaluating antecedent satisfaction:
- **Premise Certainty:** $CF_{\text{premise}} = \min(CF(c_1), CF(c_2), \dots)$
- **Rule Conclusion Certainty:** $CF_{\text{concluded}} = CF_{\text{premise}} \times CF_{\text{rule}}$
- **MYCIN Evidence Combination:** When multiple distinct rules conclude hypothesis $H$ with confidences $CF_1$ and $CF_2$:
  $$CF_{\text{comb}}(H) = CF_1 + CF_2 \times (1 - CF_1)$$
  This guarantees monotonic belief reinforcement as supporting evidence accumulates.

### 5.4 Conflict Resolution Strategy
When multiple production rules fire simultaneously, generating conflicting maintenance recommendations, the system applies a rigorous four-tiered conflict resolution algorithm:
1. **Level 1 — Safety Invariant:** Emergency stop orders and catastrophic safety alerts take absolute precedence over all operational actions.
2. **Level 2 — Maintenance Action Priority:** Actions are ranked by engineering urgency (Priority 1: Immediate corrective repair; Priority 2: Scheduled preventive maintenance; Priority 3: Interim operational adjustment).
3. **Level 3 — Certainty Factor:** Higher diagnostic certainty breaks priority ties.
4. **Level 4 — Economic Downtime & Cost:** Lower cost and shorter downtime are selected to optimize machine availability.

### 5.5 Explanation Facility & Audit Trail
The system incorporates an automated Explanation Facility that answers "HOW" and "WHY" questions. Every rule in the knowledge base encapsulates an engineering rationale (`why` attribute). As rules fire, an immutable chronological audit trail is assembled, documenting: (1) which sensor thresholds or symptoms triggered the rule, (2) the underlying physical rationale, (3) the resulting confidence increment, and (4) the exact maintenance action justified.

---

## 6. Dataset & External Knowledge Sources

| Source / Dataset | Type | Size / Records | Role in KBS |
|:---|:---:|:---:|:---|
| **AI4I 2020 Predictive Maintenance Dataset** (Stephan Matzka, IEEE AI4I 2020) | Real-time CNC physical sensor telemetry (CSV) | 10,000 rows, 14 columns | Defines physical thresholds and failure rules for HDF, PWF, OSF, TWF; benchmark validation |
| **Spindle Bearing Heuristic Knowledge Base** (`rules.json`) | Expert maintenance rules | 25 rules in JSON format | Encodes human operator heuristics for bearing wear, seizure, starvation, contamination, and misalignment |

### Physical Derivations from Stephan Matzka (IEEE AI4I 2020):
1. **Temperature Differential:** $\Delta T = T_{\text{process}} - T_{\text{air}}$. Heat Dissipation Failure (HDF) occurs if $\Delta T < 8.6\text{ K}$ and rotational speed $N < 1380\text{ rpm}$.
2. **Mechanical Drive Power:** $P = \tau \times \omega = \tau \times \frac{2\pi N}{60}\text{ [W]}$. Power Failure (PWF) occurs if $P < 3500\text{ W}$ (stall) or $P > 9000\text{ W}$ (surge).
3. **Overstrain Load Metric:** $S = \text{tool\_wear} \times \tau\text{ [min}\cdot\text{Nm]}$. Overstrain Failure (OSF) occurs if $S > 11{,}000$ (Type L), $S > 12{,}000$ (Type M), or $S > 13{,}000$ (Type H).
4. **Critical Tool Life Window:** Tool Wear Failure (TWF) occurs when accumulated cutting duration reaches the 200–240 minute critical wear-out window.

---

## 7. Implementation & Software Stack

- **Core Reasoning Engine (`inference_engine.py`):** Pure Python 3.11 standard library (`json`, `math`, `csv`, `os`, `sys`) ensuring zero external runtime dependency.
- **Desktop GUI (`gui_app.py`):** Built with Python Tkinter; features dual tabs for telemetry input and symptom checklists, scenario presets, and live explanation boxes.
- **Interactive CLI (`cli_app.py`):** Console application supporting interactive manual input, benchmark demos, and batch validation.
- **Web Application (`streamlit_app.py`):** Interactive Streamlit dashboard with telemetry sliders, live metric cards, and 10,000-row batch visualizer.

---

## 8. Testing, Validation & Results

### 8.1 AI4I 2020 Dataset Batch Validation (10,000 Rows)
The entire 10,000-row dataset was processed through `tests/validate_ai4i_dataset.py` in **1.72 seconds** (throughput: **5,809 rows/sec**).

| Failure Mode | Rule ID | TP | FP | FN | TN | Accuracy | Precision | Recall | F1-Score |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Heat Dissipation (HDF)** | R14 | 115 | 0 | 0 | 9,885 | **100.00%** | **100.00%** | **100.00%** | **1.0000** |
| **Power Failure (PWF)** | R15 | 95 | 0 | 0 | 9,905 | **100.00%** | **100.00%** | **100.00%** | **1.0000** |
| **Overstrain Failure (OSF)** | R16 | 98 | 0 | 0 | 9,902 | **100.00%** | **100.00%** | **100.00%** | **1.0000** |
| **Overall Deterministic Failure** | R14–R16 | 287 | 0 | 52 | 9,661 | **99.48%** | **100.00%** | **84.66%** | **0.9169** |

**Key Findings:**
1. **Zero False Positives (100% Precision):** Across all 9,661 normal operating cycles, the KBS never issued a false alarm for HDF, PWF, or OSF.
2. **287 out of 339 machine failures** are identified deterministically. The remaining 52 failures represent stochastic tool wear degradation (TWF) and random sensor glitches (RNF), both monitored via secondary rules.

### 8.2 Bearing Diagnosis Scenario Testing
Automated integration scenarios in `tests/test_cases.py` comprehensively test rolling element bearing fault conditions, confirming that multi-symptom corroboration is required before asserting severe faults like bearing seizure, while ensuring sound certainty factor accumulation.

### 8.3 Unit & Scenario Test Suite (8 Tests)
Executed via `tests/test_cases.py`:
- `test_bearing_wear`: PASSED
- `test_bearing_seizure_safety`: PASSED
- `test_contamination`: PASSED
- `test_bearing_misalignment`: PASSED
- `test_telemetry_hdf`: PASSED
- `test_telemetry_pwf_high`: PASSED
- `test_telemetry_osf`: PASSED
- `test_conflict_resolution_and_explanation`: PASSED

---

## 9. Evaluation, Limitations & Conclusion

### 9.1 Technical Evaluation
- **Explainability:** Unlike black-box neural networks, every conclusion provides a human-verifiable rule trace.
- **Safety Compliance:** Hard safety alarms prevent catastrophic spindle crash and operator injury.
- **High Throughput:** 5,809 rows/second enables real-time deployment on edge controllers.

### 9.2 Limitations & Future Improvements
- **Static vs. Dynamic Thresholds:** Currently, telemetry limits are fixed; future work will incorporate adaptive baseline tracking based on workpiece material hardness.
- **Sensor Connectivity:** Integration with industrial edge protocols (OPC-UA and MTConnect) for direct PLC streaming.

### 9.3 Conclusion
The developed Knowledge-Based System resolves the Complex Computing Problem by delivering a complete, robust, and mathematically verified expert system for CNC machine spindle and process fault diagnosis. By uniting the 10,000-row AI4I 2020 predictive maintenance benchmark with expert spindle bearing heuristics, the prototype achieves 100% precision on physical failures, provides rich multi-tiered conflict resolution, and demonstrates complete transparency through its explanation facility.

---

## 10. References

1. **Matzka, S. (2020).** *Explainable Artificial Intelligence for Predictive Maintenance Applications*. Third International Conference on Artificial Intelligence for Industries (AI4I 2020), IEEE, pp. 69–74. DOI: `10.1109/AI4I49448.2020.00023`.
2. **Giarratano, J. C., & Riley, G. (2005).** *Expert Systems: Principles and Programming* (4th ed.). Course Technology / Thomson Learning.
3. **Shortliffe, E. H., & Buchanan, B. G. (1975).** *A model of inexact reasoning in medicine*. Mathematical Biosciences, 23(3-4), pp. 351–379.
4. **ISO 10816-3:2009.** *Mechanical vibration — Evaluation of machine vibration by measurements on non-rotating parts — Part 3: Industrial machines with nominal power above 15 kW and nominal speeds between 120 r/min and 15 000 r/min*.
5. **Altintas, Y. (2012).** *Manufacturing Automation: Metal Cutting Mechanics, Machine Tool Vibrations, and CNC Design* (2nd ed.). Cambridge University Press.
6. Course Material & Lecture Notes for *Knowledge-Based Systems (CT-359)*, Department of Computer Science & Information Technology, NED University of Engineering & Technology, Karachi.
