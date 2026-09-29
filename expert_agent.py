"""
Simple Expert System + Intelligent Agent
Topic: Laptop problem diagnosis

Agent cycle:  PERCEIVE (ask questions)  ->  THINK (inference engine)  ->  ACT (give advice)

Expert system parts:
  1. Knowledge base    -> RULES and ADVICE
  2. Inference engine  -> forward_chain()
  3. Explanation       -> the agent shows WHICH rules produced each conclusion
"""

import sys

# ---------------------------------------------------------------------------
# 1. KNOWLEDGE BASE
# ---------------------------------------------------------------------------

# Symptoms the agent can "perceive" (fact name -> question to ask)
QUESTIONS = {
    "no_power":        "Does the laptop fail to turn on at all?",
    "charger_faulty":  "Is the charger damaged or does its light stay off?",
    "overheating":     "Does the laptop get very hot?",
    "loud_fan":        "Is the fan very loud?",
    "slow":            "Is the laptop running slowly?",
    "disk_full":       "Is the hard disk almost full (more than 90%)?",
    "no_wifi":         "Can the laptop NOT connect to Wi-Fi?",
    "other_devices_ok": "Do other devices (phone, etc.) connect to the same Wi-Fi fine?",
    "blue_screen":     "Does the laptop show a blue screen / crash?",
    "new_driver":      "Did you install a new driver or update recently?",
    "old_battery":     "Is the battery more than 3 years old?",
    "battery_drains":  "Does the battery drain very fast?",
}

# Rules:  (rule name, {conditions that must ALL be true}, conclusion)
# A conclusion can become a condition of another rule -> this is "chaining".
RULES = [
    ("R1", {"overheating", "loud_fan"},          "dust_in_fan"),
    ("R2", {"slow", "overheating"},              "cpu_throttling"),
    ("R3", {"cpu_throttling", "dust_in_fan"},    "cooling_failure"),
    ("R4", {"slow", "disk_full"},                "disk_problem"),
    ("R5", {"no_power", "charger_faulty"},       "bad_charger"),
    ("R6", {"battery_drains", "old_battery"},    "worn_battery"),
    ("R7", {"no_power", "old_battery"},          "worn_battery"),
    ("R8", {"no_wifi", "other_devices_ok"},      "wifi_adapter_problem"),
    ("R9", {"blue_screen", "new_driver"},        "bad_driver"),
]

# Final conclusions (diagnosis -> recommended action)
ADVICE = {
    "cooling_failure":      "Clean the fan and vents, replace thermal paste, use a cooling pad.",
    "dust_in_fan":          "Open the laptop and clean the dust from the fan.",
    "cpu_throttling":       "The CPU slows itself down because of heat. Improve cooling.",
    "disk_problem":         "Delete unused files or move them to an external disk.",
    "bad_charger":          "Try another charger. Replace the current one.",
    "worn_battery":         "Replace the battery.",
    "wifi_adapter_problem": "Restart the Wi-Fi adapter and update/reinstall its driver.",
    "bad_driver":           "Roll back the last driver in Device Manager.",
}


# ---------------------------------------------------------------------------
# 2. INFERENCE ENGINE (forward chaining)
# ---------------------------------------------------------------------------

def forward_chain(facts):
    """
    Repeatedly apply the rules to the known facts until nothing new is found.
    Returns a list describing which rule fired (used for explanation).
    """
    trace = []
    changed = True
    while changed:                                   # keep going while we learn something
        changed = False
        for name, conditions, conclusion in RULES:
            # conditions <= facts  means: ALL conditions are inside facts (subset check)
            if conditions <= facts and conclusion not in facts:
                facts.add(conclusion)                # new knowledge
                trace.append((name, conditions, conclusion))
                changed = True
    return trace


# ---------------------------------------------------------------------------
# 3. THE AGENT
# ---------------------------------------------------------------------------

class LaptopExpertAgent:
    def __init__(self, sensor):
        self.sensor = sensor     # a function that answers a question with True / False
        self.facts = set()       # what the agent currently knows
        self.trace = []          # which rules fired

    def perceive(self):
        """Collect information from the environment (the user)."""
        print("\n--- PERCEIVE: answer the questions ---")
        for fact, question in QUESTIONS.items():
            if self.sensor(question):
                self.facts.add(fact)

    def think(self):
        """Use the inference engine to derive new facts."""
        self.trace = forward_chain(self.facts)

    def act(self):
        """Give advice and explain the reasoning."""
        print("\n--- THINK: rules that fired ---")
        if not self.trace:
            print("No rule matched.")
        for name, conditions, conclusion in self.trace:
            print(f"{name}: IF {' AND '.join(sorted(conditions))} THEN {conclusion}")

        print("\n--- ACT: diagnosis and advice ---")
        found = [f for f in self.facts if f in ADVICE]
        if not found:
            print("I could not find a problem. Please contact a technician.")
        for diagnosis in found:
            print(f"* {diagnosis}: {ADVICE[diagnosis]}")

    def run(self):
        self.perceive()
        self.think()
        self.act()


# ---------------------------------------------------------------------------
# Sensors (two ways to get answers)
# ---------------------------------------------------------------------------

def ask_user(question):
    """Interactive sensor: asks the real user in the terminal."""
    while True:
        answer = input(f"{question} (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please type y or n.")


def make_demo_sensor(true_questions):
    """Demo sensor: automatically answers 'yes' only for the chosen facts."""
    def sensor(question):
        for fact, text in QUESTIONS.items():
            if text == question:
                answer = fact in true_questions
                print(f"{question} -> {'y' if answer else 'n'}")
                return answer
        return False
    return sensor


if __name__ == "__main__":
    if "--demo" in sys.argv:
        # Test scenario: hot, loud and slow laptop
        agent = LaptopExpertAgent(make_demo_sensor({"overheating", "loud_fan", "slow"}))
    else:
        agent = LaptopExpertAgent(ask_user)
    agent.run()
