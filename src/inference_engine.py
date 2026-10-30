"""
Rule-Based Inference Engine for CNC Spindle & Process Fault Diagnosis
Knowledge-Based Systems (CT-359) — Complex Computing Problem (CCP)

Supports:
1. Operator Heuristic Symptom Diagnosis (Spindle bearings, lubrication, misalignment)
2. Real-Time Telemetry Diagnosis based on AI4I 2020 Predictive Maintenance (Stephan Matzka, IEEE 2020)
3. Forward-Chaining Inference with Certainty Factors (MYCIN-style)
4. Comprehensive Explanation Facility and Conflict Resolution (Safety -> CF -> Cost)
"""

import json
import math
import os


class KnowledgeBase:
    def __init__(self, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.domain = data.get("domain", "CNC Spindle & Process Fault Diagnosis")
        self.version = data.get("version", "3.0")
        self.description = data.get("description", "")
        self.equipment = data.get("equipment", {})
        self.symptoms = data.get("symptoms", [])
        self.faults = data.get("faults", [])
        self.actions = data.get("actions", {})
        self.rules = data.get("rules", [])


class InferenceEngine:
    def __init__(self, kb):
        self.kb = kb
        self.facts = {}            # fact_name -> certainty factor (-1.0 to 1.0, typically 0.0 to 1.0)
        self.fired = []            # list of rule IDs fired in sequence
        self.explanations = []     # human-readable audit trail
        self.safety_messages = []  # prioritized safety notices

    def add_fact(self, name, cf=1.0):
        """Add an arbitrary fact or symptom with its certainty factor."""
        self.facts[name] = max(-1.0, min(1.0, float(cf)))

    def add_symptoms(self, symptom_list):
        """Add symptoms with full certainty (1.0)."""
        for s in symptom_list:
            if s in self.kb.symptoms:
                self.facts[s] = 1.0
            else:
                # Still allow user custom or telemetry facts
                self.facts[s] = 1.0

    def _all_present(self, conditions):
        """Check if all antecedent conditions are present with positive CF."""
        for c in conditions:
            if c not in self.facts or self.facts[c] <= 0:
                return False
        return True

    def _min_cf(self, conditions):
        """Compute the premise certainty factor (fuzzy conjunction / min rule)."""
        return min(self.facts[c] for c in conditions)

    def run(self):
        """
        Forward Chaining with Certainty Factors:
        Iterates over the rule base until no further rules can fire.
        Updates working memory and resolves conflicts by accumulating evidence.
        """
        changed = True
        while changed:
            changed = False
            for rule in self.kb.rules:
                rule_id = rule["id"]
                if rule_id in self.fired:
                    continue

                if self._all_present(rule["if"]):
                    premise_cf = self._min_cf(rule["if"])
                    rule_cf = rule.get("cf", 1.0)
                    concluded_cf = premise_cf * rule_cf

                    # 1. Fault conclusion
                    if "then_fault" in rule:
                        fault_key = "fault:" + rule["then_fault"]
                        if fault_key in self.facts:
                            # Standard MYCIN evidence combination: CF_comb = CF1 + CF2 * (1 - CF1)
                            old_cf = self.facts[fault_key]
                            if old_cf >= 0 and concluded_cf >= 0:
                                combined = old_cf + (concluded_cf * (1.0 - old_cf))
                            else:
                                combined = max(old_cf, concluded_cf)
                            self.facts[fault_key] = round(combined, 4)
                        else:
                            self.facts[fault_key] = round(concluded_cf, 4)

                        self.explanations.append(
                            f"Rule {rule_id} fired: {rule['why']} -> {rule['then_fault']} (CF={self.facts[fault_key]:.2f})"
                        )

                    # 2. Maintenance Action conclusion
                    elif "then_action" in rule:
                        action_id = rule["then_action"]
                        action_key = "action:" + action_id
                        if action_key in self.facts:
                            old_cf = self.facts[action_key]
                            combined = old_cf + (concluded_cf * (1.0 - old_cf))
                            self.facts[action_key] = round(combined, 4)
                        else:
                            self.facts[action_key] = round(concluded_cf, 4)

                        act_info = self.kb.actions.get(action_id, {})
                        act_name = act_info.get("name", action_id)
                        self.explanations.append(
                            f"Rule {rule_id} fired: Recommend Action [{action_id}] '{act_name}' — {rule['why']} (CF={self.facts[action_key]:.2f})"
                        )

                    # 3. Urgent Safety Alert conclusion
                    elif "then_safety" in rule:
                        msg = rule["then_safety"]
                        if msg not in self.safety_messages:
                            self.safety_messages.append(msg)
                        self.explanations.append(
                            f"Rule {rule_id} [SAFETY ENFORCEMENT]: {rule['why']}"
                        )

                    self.fired.append(rule_id)
                    changed = True

        return self.get_results()

    def get_results(self):
        """
        Extract and format diagnosis results with conflict resolution:
        Priority is sorted by:
        1. Safety alerts first
        2. Maintenance actions sorted by safety priority (1 = highest) -> CF (descending) -> Cost
        """
        diagnosed = {}
        recommended = []

        cost_weights = {"Very Low": 1, "Low": 2, "Medium": 3, "High": 4}

        for fact, cf in self.facts.items():
            if fact.startswith("fault:"):
                fault_name = fact[6:]
                diagnosed[fault_name] = round(cf, 3)

            elif fact.startswith("action:"):
                aid = fact[7:]
                info = self.kb.actions.get(aid, {
                    "name": aid,
                    "priority": 3,
                    "cost": "Medium",
                    "downtime": "Unknown",
                    "who": "Technician"
                })

                recommended.append({
                    "id": aid,
                    "name": info["name"],
                    "action": info["name"],                       # Streamlit compatibility
                    "cf": round(cf, 3),
                    "priority": info["priority"],
                    "safety_priority": info["priority"],         # Streamlit compatibility
                    "cost": info["cost"],
                    "downtime": info["downtime"],
                    "downtime_hours": info["downtime"],          # Streamlit compatibility
                    "who": info["who"],
                    "skill": info["who"],                        # Streamlit compatibility
                    "_cost_w": cost_weights.get(info["cost"], 5)
                })

        # Conflict resolution sorting: Priority ascending (1 before 2), then CF descending, then Cost ascending
        recommended.sort(key=lambda x: (x["priority"], -x["cf"], x["_cost_w"]))

        # Build clean formatted explanation text
        explanation_lines = [
            f"=== Knowledge-Based Inference Audit Trail ===",
            f"Fired Rules Count: {len(self.fired)}",
            f"Active Facts in Working Memory: {len(self.facts)}",
            ""
        ]
        for e in self.explanations:
            explanation_lines.append(f"• {e}")

        explanation_text = "\n".join(explanation_lines)

        return {
            # Legacy & GUI keys
            "faults": diagnosed,
            "actions": recommended,
            "safety": self.safety_messages,
            "explanations": self.explanations,
            "fired_rules": self.fired,

            # Streamlit & Rich interface keys
            "diagnosed_faults": diagnosed,
            "recommended_actions": recommended,
            "safety_alerts": self.safety_messages,
            "explanation_text": explanation_text,
            "working_memory": self.facts
        }


def get_default_kb_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "knowledge_base", "rules.json")


def diagnose(symptoms, rules_path=None):
    """
    Standard diagnosis entry point used by Tkinter GUI, CLI, and test cases.
    """
    path = rules_path or get_default_kb_path()
    kb = KnowledgeBase(path)
    engine = InferenceEngine(kb)
    engine.add_symptoms(symptoms)
    return engine.run()


def run_diagnosis(symptoms, rules_path=None):
    """
    Alias function compatible with Streamlit and external callers.
    """
    return diagnose(symptoms, rules_path)


def diagnose_telemetry(air_temp_k, process_temp_k, speed_rpm, torque_nm, tool_wear_min, product_type="M", rules_path=None):
    """
    Evaluates real-time sensor measurements from CNC machine telemetry
    (AI4I 2020 Predictive Maintenance Dataset standard by Stephan Matzka, IEEE 2020).

    Physics & Engineering Rules:
    1. Temperature Delta: delta_T = Process_Temp - Air_Temp
       - Heat Dissipation Failure (HDF) if delta_T < 8.6 K and speed < 1380 rpm
    2. Mechanical Drive Power: P = Torque * omega = Torque * (2 * pi * speed / 60) in Watts
       - Power Failure (PWF) if P < 3500 W or P > 9000 W
    3. Overstrain Load Metric: S = tool_wear * torque
       - Overstrain Failure (OSF) if S > 11,000 (L), 12,000 (M), or 13,000 (H) min*Nm
    4. Tool Life Expiration:
       - Tool Wear Failure (TWF) warning if tool_wear in [200, 240] min
    """
    path = rules_path or get_default_kb_path()
    kb = KnowledgeBase(path)
    engine = InferenceEngine(kb)

    # Derived physical quantities
    delta_T = float(process_temp_k) - float(air_temp_k)
    omega = (float(speed_rpm) * 2.0 * math.pi) / 60.0
    power_watts = float(torque_nm) * omega
    overstrain_val = float(tool_wear_min) * float(torque_nm)

    ptype = str(product_type).upper()
    osf_limits = {"L": 11000.0, "M": 12000.0, "H": 13000.0}
    osf_limit = osf_limits.get(ptype, 12000.0)

    derived_symptoms = []

    # Check HDF predicate
    if delta_T < 8.6 and float(speed_rpm) < 1380.0:
        derived_symptoms.append("heat_dissipation_hazard")
        engine.add_fact("heat_dissipation_hazard", 1.0)

    # Check PWF predicate
    if power_watts < 3500.0 or power_watts > 9000.0:
        derived_symptoms.append("power_surge_or_stall")
        engine.add_fact("power_surge_or_stall", 1.0)

    # Check OSF predicate
    if overstrain_val > osf_limit:
        derived_symptoms.append("critical_overstrain")
        engine.add_fact("critical_overstrain", 1.0)

    # Check TWF predicate
    if float(tool_wear_min) >= 200.0:
        derived_symptoms.append("excessive_tool_wear")
        # Scale CF linearly between 200 and 240
        cf_tw = min(1.0, 0.60 + 0.40 * ((float(tool_wear_min) - 200.0) / 40.0))
        engine.add_fact("excessive_tool_wear", cf_tw)

    # Run inference
    results = engine.run()

    # Append telemetry diagnostics summary to results
    results["telemetry_metrics"] = {
        "delta_T_K": round(delta_T, 2),
        "angular_velocity_rad_s": round(omega, 2),
        "power_watts": round(power_watts, 2),
        "overstrain_min_Nm": round(overstrain_val, 2),
        "overstrain_limit": osf_limit,
        "product_type": ptype,
        "derived_symptoms": derived_symptoms
    }

    return results


def evaluate_ai4i_row(row_dict, rules_path=None):
    """
    Convenience method to diagnose a single dictionary row from ai4i2020.csv
    """
    return diagnose_telemetry(
        air_temp_k=float(row_dict["Air temperature [K]"]),
        process_temp_k=float(row_dict["Process temperature [K]"]),
        speed_rpm=float(row_dict["Rotational speed [rpm]"]),
        torque_nm=float(row_dict["Torque [Nm]"]),
        tool_wear_min=float(row_dict["Tool wear [min]"]),
        product_type=row_dict.get("Type", "M"),
        rules_path=rules_path
    )


if __name__ == "__main__":
    print("=== Testing Updated Inference Engine ===")
    r1 = diagnose(["unusual_noise", "high_vibration"])
    print("Symptom Test (Noise + Vibration):", r1["faults"], [a["name"] for a in r1["actions"]])

    print("\nTelemetry Test (HDF Scenario): Air=298.9K, Proc=306.0K (delta=7.1K), Speed=1350rpm")
    r2 = diagnose_telemetry(298.9, 306.0, 1350, 45.0, 10, "M")
    print("Faults:", r2["faults"])
    print("Actions:", [a["name"] for a in r2["actions"]])
    print("Telemetry Metrics:", r2["telemetry_metrics"])
