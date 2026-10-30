# Viva Defense & Presentation Guide
## Complex Computing Problem (CCP) — Course: Knowledge-Based Systems (CT-359)
**Project Title:** Intelligent Knowledge-Based System for CNC Spindle & Process Fault Diagnosis and Predictive Maintenance Support

---

## 1. Quick 2-Minute Elevator Pitch for the Examiner

> "Good morning, respected examiner. Our project addresses industrial predictive maintenance for CNC Vertical Machining Centers. 
> CNC spindle failures, such as bearing seizure, heat dissipation failure, or tool overstrain, cause severe financial downtime, workpiece scrapping, and operator safety hazards.
> 
> Rather than relying on opaque black-box neural networks that cannot explain their reasoning, we engineered an intelligent, transparent Knowledge-Based System using Forward Chaining and MYCIN Certainty Factors.
> 
> What makes our system unique is its dual-module architecture:
> 1. It models physical sensor telemetry validated against the benchmark AI4I 2020 Predictive Maintenance Dataset (10,000 real-world CNC milling cycles by Stephan Matzka, IEEE 2020), achieving 100% precision with zero false alarms.
> 2. It incorporates human workshop heuristics for rolling bearing mechanical failures.
> 
> The system enforces real-time emergency safety stops, multi-tiered conflict resolution, and provides a complete explanation audit trail for every fired rule. We have implemented it with zero external dependencies in Python Tkinter GUI, CLI, and Streamlit."

---

## 2. Likely Viva Questions & Model Answers

### Q1: Why did you choose a Rule-Based KBS instead of Machine Learning or Deep Learning?
**Answer:**
- **Explainability:** In industrial manufacturing, if a machine is halted, the maintenance engineer must know *why*. Neural networks are black boxes; our KBS provides a rule-by-rule audit trail justifying every conclusion.
- **Safety Invariants:** A neural network can output a false negative with non-zero probability. Our KBS enforces deterministic safety invariants (e.g., if severe overstrain or bearing seizure occurs, the machine MUST stop immediately).
- **Data Scarcity for Rare Catastrophic Failures:** True bearing seizures happen rarely. Machine learning lacks sufficient positive examples, whereas engineering production rules directly capture physical laws (e.g., $P = \tau \times \omega$, thermodynamics of heat dissipation).

### Q2: What dataset did you use and why is it suitable for Knowledge-Based Systems?
**Answer:**
- We used the **AI4I 2020 Predictive Maintenance Dataset** by Stephan Matzka (published in IEEE AI4I 2020).
- It contains **10,000 operational cycles** of a CNC milling machine across 14 variables.
- It is ideal for KBS because each failure mode is grounded in documented mechanical and thermodynamic failure criteria:
  - **Heat Dissipation Failure (HDF):** Convective thermal delta $\Delta T < 8.6\text{ K}$ and rotational speed $N < 1380\text{ rpm}$.
  - **Power Failure (PWF):** Required mechanical power $P = \tau \times \omega < 3500\text{ W}$ or $> 9000\text{ W}$.
  - **Overstrain Failure (OSF):** Tool wear $\times$ torque exceeds product variant limits (11,000 for L, 12,000 for M, 13,000 for H $\text{min}\cdot\text{Nm}$).
- Validating against all 10,000 rows, our KBS achieved **100% Precision** (0 false positives) and **99.48% overall accuracy**.

### Q3: How do you handle uncertainty in the system?
**Answer:**
- We implemented the **MYCIN Certainty Factor (CF) model** developed by Shortliffe and Buchanan.
- Certainty factors range from 0.0 (no confidence) to 1.0 (absolute certainty).
- When evaluating rule premises with multiple conditions, we apply the fuzzy conjunction min-rule:
  $$CF_{\text{premise}} = \min(CF_1, CF_2, \dots)$$
- When multiple independent rules conclude the same fault hypothesis, we combine their confidences using the asymptotic MYCIN combination formula:
  $$CF_{\text{comb}} = CF_1 + CF_2 \times (1 - CF_1)$$
- This ensures that accumulating evidence monotonically strengthens belief without ever exceeding 1.0.

### Q4: How does your Conflict Resolution strategy work?
**Answer:**
- If multiple rules fire simultaneously and suggest contradictory or competing actions, our system uses a 4-level hierarchy:
  1. **Level 1 (Safety Invariant):** Immediate emergency stop orders and safety alerts always override operational actions.
  2. **Level 2 (Maintenance Urgency Priority):** Priority 1 (immediate repair, e.g., tool/bearing replacement) before Priority 2 (oil flush) before Priority 3 (load de-rating).
  3. **Level 3 (Confidence / CF):** Higher Certainty Factor breaks ties among equal priorities.
  4. **Level 4 (Economic Cost & Downtime):** Shorter downtime and lower cost are selected to optimize machine availability.

### Q5: What are the Complex Computing Problem (CCP) attributes addressed in your project?
**Answer:**
- **CPA-2 (Depth of Engineering Knowledge):** Derives physical formulas for spindle power $P = \tau \times \frac{2\pi N}{60}$, convective heat transfer, and torsional shear wear.
- **CPA-3 (Depth of Analysis):** Evaluates incomplete and conflicting operator symptoms, noisy sensor readings, and multi-tiered trade-offs between safety stops and downtime costs.
- **CPA-9 (Societal, Safety & Standards):** Prevents mechanical projectile hazards from exploding cutters, enforces worker safety, and aligns with ISO 10816 industrial vibration standards.

---

## 3. Step-by-Step Live Demo Instructions

During your viva presentation, you can demonstrate the project across 3 interfaces:

### Demo Step 1: Desktop GUI (Tkinter)
Run command:
```bash
python src/gui_app.py
```
1. Click on **Tab 1: Sensor Telemetry Diagnosis**.
2. Click the preset button **"HDF (Heat Dissipation)"** -> Note air temp = 298.9 K, proc temp = 306.0 K ($\Delta T = 7.1\text{ K} < 8.6\text{ K}$), speed = 1350 rpm.
3. Click **"Run Telemetry Diagnosis"** -> Show the examiner:
   - Concluded Fault: `HEAT DISSIPATION FAILURE` (Confidence = 0.98).
   - Recommended Action: `[A8] Service heat exchanger and flush spindle coolant jacket`.
   - Explanation Facility: Walk the examiner through the bulleted physical audit trail!
4. Click the preset button **"OSF (Overstrain)"** -> Show tool wear = 215 min, torque = 58 Nm on Type L ($215 \times 58 = 12,470 > 11,000$).
   - Point out the red **CRITICAL SAFETY ALERT**: *"HIGH MECHANICAL STRESS WARNING"*.
5. Switch to **Tab 2: Operator Heuristic Symptoms**.
   - Check `Unusual noise` + `High vibration` + `Spindle overheating`.
   - Click **Diagnose** -> Point out `bearing_seizure` and the **EMERGENCY STOP** alarm.

### Demo Step 2: 10,000-Row Dataset Batch Validation
Run command:
```bash
python tests/validate_ai4i_dataset.py
```
- Show the examiner the live output:
  - Processed 10,000 rows in ~1.7 seconds.
  - HDF: 100% Precision, 100% Recall.
  - PWF: 100% Precision, 100% Recall.
  - OSF: 100% Precision, 100% Recall.
  - Overall accuracy: **99.48% with 0 False Positives** across 9,661 normal operating cycles.

### Demo Step 3: Streamlit Web Dashboard (Optional)
Run command:
```bash
streamlit run src/streamlit_app.py
```
- Show the browser interface with live interactive sliders, gauge metrics, and the batch evaluation tab.
