"""
SMART COMMUTE AI
================
ML + Goal-Based AI Agent + Planning

Architecture:
    Environment -> ML Predictor -> AI Planner -> Route Evaluation
    -> Action -> New Environment State -> Re-planning

The ML model predicts travel time.
The AI agent uses those predictions to choose a route.

This is NOT an LLM agent. It combines:
    - Machine Learning
    - Search / Planning
    - Goal-based reasoning
    - Dynamic re-planning
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Set

import numpy as np
from sklearn.ensemble import RandomForestRegressor


# ============================================================
# 1. ROAD
# ============================================================

@dataclass
class Road:
    destination: str
    mode: str
    base_minutes: int       # normal/base travel time
    cost: float
    traffic: int = 0        # 0 = free, 1 = normal, 2 = heavy


# ============================================================
# 2. ENVIRONMENT
# ============================================================

class CommuteEnvironment:

    def __init__(self):
        self.city: Dict[str, List[Road]] = {}
        self.blocked_modes: Set[str] = set()
        self.build_city()

    def connect(self, a, b, mode, minutes, cost, traffic=0):
        self.city.setdefault(a, []).append(Road(b, mode, minutes, cost, traffic))
        self.city.setdefault(b, []).append(Road(a, mode, minutes, cost, traffic))

    def build_city(self):
        self.connect("Home", "Bus Stop", "walk", 5, 0.0)
        self.connect("Home", "Metro A", "walk", 15, 0.0)
        self.connect("Home", "University", "taxi", 25, 12.0)
        self.connect("Bus Stop", "Metro A", "bus", 10, 0.5, traffic=1)
        self.connect("Bus Stop", "University", "bus", 45, 0.6, traffic=2)
        self.connect("Metro A", "Metro B", "metro", 12, 0.5)
        self.connect("Metro A", "University", "taxi", 15, 8.0, traffic=1)
        self.connect("Metro B", "University", "walk", 10, 0.0)
        self.connect("Metro B", "University", "taxi", 4, 3.0, traffic=1)

    def close_mode(self, mode):
        self.blocked_modes.add(mode)

    def is_available(self, road):
        return road.mode not in self.blocked_modes


# ============================================================
# 3. MACHINE LEARNING MODEL
# ============================================================

class TravelTimePredictor:
    """
    Learns: traffic + mode + base travel time -> predicted travel time
    """

    MODES = {"walk": 0, "bus": 1, "metro": 2, "taxi": 3}

    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.train()

    def train(self):
        # Synthetic historical data.
        # In a real project: Google Maps / traffic APIs / GPS / transport data.
        random.seed(42)

        traffic_multiplier = {0: 1.0, 1: 1.25, 2: 1.60}
        mode_delay = {0: 0, 1: 2, 2: 0, 3: 4}   # walk, bus, metro, taxi

        X, y = [], []

        for _ in range(1000):
            base_time = random.randint(5, 60)
            traffic = random.randint(0, 2)
            mode = random.randint(0, 3)
            noise = random.uniform(-2, 2)

            actual_time = (
                base_time * traffic_multiplier[traffic]
                + mode_delay[mode]
                + noise
            )

            X.append([base_time, traffic, mode])
            y.append(actual_time)

        self.model.fit(np.array(X), np.array(y))

    def mode_to_number(self, mode):
        return self.MODES[mode]

    def predict(self, road: Road):
        features = np.array([[
            road.base_minutes,
            road.traffic,
            self.mode_to_number(road.mode),
        ]])
        return round(float(self.model.predict(features)[0]), 1)


# ============================================================
# 4. AI AGENT
# ============================================================

class SmartCommuteAgent:

    def __init__(self, environment, predictor, start, goal,
                 deadline, budget, strategy="balanced"):
        self.environment = environment
        self.predictor = predictor
        self.location = start
        self.goal = goal
        self.deadline = deadline
        self.budget = budget
        self.strategy = strategy
        self.time_used = 0
        self.money_spent = 0
        self.plan = []

    # ---------------- Goal test ----------------

    def goal_reached(self):
        return self.location == self.goal

    # ---------------- Observation ----------------

    def observe(self):
        print("\n🧠 AGENT OBSERVATION")
        print(f"Location: {self.location}")
        print(f"Time used: {self.time_used:.1f} min")
        print(f"Money spent: {self.money_spent:.2f} AZN")
        print(f"Remaining time: {self.deadline - self.time_used:.1f} min")
        print(f"Remaining budget: {self.budget - self.money_spent:.2f} AZN")

        if self.environment.blocked_modes:
            print("Blocked modes:", self.environment.blocked_modes)

    # ---------------- Route score ----------------

    def score(self, time, cost):
        if self.strategy == "fastest":
            return time
        if self.strategy == "cheapest":
            return cost
        return time + 5 * cost   # balanced

    # ---------------- Planning ----------------

    def make_plan(self):
        print("\n🔎 AI PLANNER")
        print("Searching possible future states...")

        best_plan = None
        best_score = float("inf")

        stack = [(self.location, [], self.time_used, self.money_spent)]

        while stack:
            place, route, current_time, current_cost = stack.pop()

            # Goal reached
            if place == self.goal:
                route_time = current_time - self.time_used
                route_cost = current_cost - self.money_spent
                route_score = self.score(route_time, route_cost)

                if route_score < best_score:
                    best_score = route_score
                    best_plan = route
                continue

            # Explore possible actions
            for road in self.environment.city.get(place, []):

                if not self.environment.is_available(road):
                    continue

                # ML prediction
                new_time = current_time + self.predictor.predict(road)
                new_cost = current_cost + road.cost

                # Constraints
                if new_time > self.deadline or new_cost > self.budget:
                    continue

                # Avoid cycles
                visited = {self.location} | {r.destination for r in route}
                if road.destination in visited:
                    continue

                stack.append((road.destination, route + [road], new_time, new_cost))

        if best_plan is None:
            return None

        print("✓ Best plan found")
        print(f"✓ Score: {best_score:.2f}")
        return best_plan

    # ---------------- Show plan ----------------

    def show_plan(self, plan):
        print("\n📋 AI SELECTED PLAN")

        current = self.location
        total_time = 0
        total_cost = 0

        for i, road in enumerate(plan, 1):
            predicted = self.predictor.predict(road)
            total_time += predicted
            total_cost += road.cost

            print(f"{i}. {current} --[{road.mode}]--> {road.destination}")
            print(f"   ML predicted time: {predicted:.1f} min")
            print(f"   Cost: {road.cost:.2f} AZN")

            current = road.destination

        print("\nEstimated total:")
        print(f"Time: {total_time:.1f} min")
        print(f"Cost: {total_cost:.2f} AZN")

    # ---------------- Execute action ----------------

    def execute(self, road):
        predicted_time = self.predictor.predict(road)

        print("\n🤖 ACTION")
        print(f"{self.location} → {road.destination}")
        print(f"Transport: {road.mode}")
        print(f"ML predicted travel time: {predicted_time:.1f} min")

        self.location = road.destination
        self.time_used += predicted_time
        self.money_spent += road.cost

    # ---------------- Re-planning ----------------

    def replan(self):
        print("\n🔄 RE-PLANNING")
        print("The environment changed.")
        print("AI is searching for a new route...")

        self.plan = self.make_plan()

        if self.plan:
            self.show_plan(self.plan)

    # ---------------- Run ----------------

    def run(self, events=None):
        events = events or {}

        print("\n" + "=" * 65)
        print("🤖 SMART COMMUTE AI AGENT")
        print("=" * 65)
        print(f"Goal: {self.goal}")
        print(f"Deadline: {self.deadline} min")
        print(f"Budget: {self.budget:.2f} AZN")
        print(f"Strategy: {self.strategy}")

        # Initial observation and plan
        self.observe()
        self.plan = self.make_plan()

        if not self.plan:
            print("\n❌ No valid route.")
            return

        self.show_plan(self.plan)

        # Agent loop
        while not self.goal_reached():

            if not self.plan:
                self.replan()

                if not self.plan:
                    print("\n❌ Mission failed.")
                    return

            action = self.plan.pop(0)
            self.execute(action)
            self.observe()

            # Environment event
            if self.location in events and not self.goal_reached():
                closed = events[self.location]

                print("\n🚨 ENVIRONMENT CHANGE")
                print(f"⚠️ {closed.upper()} is now unavailable!")

                self.environment.close_mode(closed)
                self.replan()

        # Success
        print("\n" + "=" * 65)
        print("🎯 GOAL REACHED")
        print(f"Destination: {self.location}")
        print(f"Total time: {self.time_used:.1f} min")
        print(f"Total cost: {self.money_spent:.2f} AZN")
        print(f"Deadline: {self.deadline} min")
        print(f"Budget: {self.budget:.2f} AZN")
        print("=" * 65)


# ============================================================
# 5. MAIN
# ============================================================

if __name__ == "__main__":

    print("Training ML travel-time predictor...")
    predictor = TravelTimePredictor()
    print("✓ ML model trained.")

    environment = CommuteEnvironment()

    agent = SmartCommuteAgent(
        environment=environment,
        predictor=predictor,
        start="Home",
        goal="University",
        deadline=70,
        budget=5,
        strategy="balanced",
    )

    # Run with dynamic environment
    agent.run(events={"Metro A": "metro"})
