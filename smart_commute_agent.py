"""
AI Smart Commute Agent
----------------------

A Goal-Based AI Agent that plans a journey from Home to University.

The agent:
1. Observes the environment.
2. Generates possible routes.
3. Evaluates routes using time, cost and risk.
4. Chooses the best valid plan.
5. Executes actions.
6. Detects environmental changes.
7. Re-plans when necessary.

This is Classical / Symbolic AI, not Machine Learning.
"""

from dataclasses import dataclass
from typing import List, Dict, Set


# ============================================================
# 1. DATA STRUCTURES
# ============================================================

@dataclass
class Road:
    destination: str
    mode: str
    minutes: int
    cost: float


@dataclass
class State:
    location: str
    time_used: int
    money_spent: float


# ============================================================
# 2. ENVIRONMENT
# ============================================================

class CommuteEnvironment:

    def __init__(self):
        self.city: Dict[str, List[Road]] = {}
        self.blocked_modes: Set[str] = set()

        self.build_city()

    def connect(
        self,
        a: str,
        b: str,
        mode: str,
        minutes: int,
        cost: float
    ):
        """Create a two-way road."""

        self.city.setdefault(a, []).append(
            Road(b, mode, minutes, cost)
        )

        self.city.setdefault(b, []).append(
            Road(a, mode, minutes, cost)
        )

    def build_city(self):

        # Walking
        self.connect(
            "Home",
            "Bus Stop",
            "walk",
            5,
            0.0
        )

        self.connect(
            "Home",
            "Metro A",
            "walk",
            15,
            0.0
        )

        # Taxi
        self.connect(
            "Home",
            "University",
            "taxi",
            25,
            12.0
        )

        # Bus
        self.connect(
            "Bus Stop",
            "Metro A",
            "bus",
            10,
            0.5
        )

        self.connect(
            "Bus Stop",
            "University",
            "bus",
            45,
            0.6
        )

        # Metro
        self.connect(
            "Metro A",
            "Metro B",
            "metro",
            12,
            0.5
        )

        # Taxi from Metro A
        self.connect(
            "Metro A",
            "University",
            "taxi",
            15,
            8.0
        )

        # Walking from Metro B
        self.connect(
            "Metro B",
            "University",
            "walk",
            10,
            0.0
        )

        # Taxi from Metro B
        self.connect(
            "Metro B",
            "University",
            "taxi",
            4,
            3.0
        )

    def close_mode(self, mode: str):
        """Environment event: a transportation mode becomes unavailable."""

        self.blocked_modes.add(mode)

    def is_available(self, road: Road) -> bool:
        return road.mode not in self.blocked_modes


# ============================================================
# 3. AI AGENT
# ============================================================

class SmartCommuteAgent:

    def __init__(
        self,
        environment: CommuteEnvironment,
        start: str,
        goal: str,
        deadline: int,
        budget: float,
        strategy: str = "balanced"
    ):

        self.environment = environment

        self.state = State(
            location=start,
            time_used=0,
            money_spent=0.0
        )

        self.goal = goal
        self.deadline = deadline
        self.budget = budget
        self.strategy = strategy

        self.plan: List[Road] = []

    # ========================================================
    # GOAL TEST
    # ========================================================

    def goal_reached(self) -> bool:
        return self.state.location == self.goal

    # ========================================================
    # STATE OBSERVATION
    # ========================================================

    def observe(self):
        print("\n🧠 AI OBSERVATION")
        print(f"   Location      : {self.state.location}")
        print(f"   Time used     : {self.state.time_used} min")
        print(f"   Money spent   : {self.state.money_spent:.2f} AZN")
        print(f"   Time left     : "
              f"{self.deadline - self.state.time_used} min")
        print(f"   Budget left   : "
              f"{self.budget - self.state.money_spent:.2f} AZN")

        if self.environment.blocked_modes:
            print(
                f"   Blocked modes : "
                f"{', '.join(self.environment.blocked_modes)}"
            )

    # ========================================================
    # ROUTE SCORING
    # ========================================================

    def evaluate_route(
        self,
        minutes: int,
        cost: float
    ) -> float:

        if self.strategy == "fastest":
            return minutes

        if self.strategy == "cheapest":
            return cost

        # Balanced strategy
        #
        # 1 AZN = approximately 5 minutes
        return minutes + 5 * cost

    # ========================================================
    # AI PLANNING
    # ========================================================

    def plan_route(self):

        print("\n🔎 AI PLANNING")
        print("   Searching possible futures...")

        best_route = None
        best_score = float("inf")

        # location, route, total time, total cost
        stack = [
            (
                self.state.location,
                [],
                self.state.time_used,
                self.state.money_spent
            )
        ]

        visited_paths = 0

        while stack:

            location, route, total_time, total_cost = stack.pop()

            # ------------------------------------------------
            # GOAL TEST
            # ------------------------------------------------

            if location == self.goal:

                route_time = total_time - self.state.time_used
                route_cost = total_cost - self.state.money_spent

                score = self.evaluate_route(
                    route_time,
                    route_cost
                )

                visited_paths += 1

                if score < best_score:
                    best_score = score
                    best_route = route

                continue

            # ------------------------------------------------
            # EXPAND POSSIBLE ACTIONS
            # ------------------------------------------------

            for road in self.environment.city.get(location, []):

                # Transportation unavailable
                if not self.environment.is_available(road):
                    continue

                new_time = total_time + road.minutes
                new_cost = total_cost + road.cost

                # Deadline constraint
                if new_time > self.deadline:
                    continue

                # Budget constraint
                if new_cost > self.budget:
                    continue

                # Avoid cycles
                locations_in_route = {
                    self.state.location
                }

                for previous_road in route:
                    locations_in_route.add(
                        previous_road.destination
                    )

                if road.destination in locations_in_route:
                    continue

                new_route = route + [road]

                stack.append(
                    (
                        road.destination,
                        new_route,
                        new_time,
                        new_cost
                    )
                )

        if best_route is None:

            print("   ❌ No valid route found.")

            return None

        print(f"   ✓ {visited_paths} possible routes evaluated.")

        print(
            f"   ✓ Best score: {best_score:.2f}"
        )

        return best_route

    # ========================================================
    # PLAN DISPLAY
    # ========================================================

    def show_plan(self, plan):

        if not plan:
            return

        total_time = sum(
            road.minutes for road in plan
        )

        total_cost = sum(
            road.cost for road in plan
        )

        print("\n📋 SELECTED PLAN")

        print(
            f"   Estimated time : {total_time} min"
        )

        print(
            f"   Estimated cost : {total_cost:.2f} AZN"
        )

        current = self.state.location

        for index, road in enumerate(plan, 1):

            print(
                f"   {index}. "
                f"{current} "
                f"--[{road.mode}]--> "
                f"{road.destination} "
                f"({road.minutes} min, "
                f"{road.cost:.2f} AZN)"
            )

            current = road.destination

    # ========================================================
    # ACTION
    # ========================================================

    def execute_action(self, road: Road):

        print(
            f"\n🤖 ACTION: "
            f"{road.mode.upper()} "
            f"{self.state.location} → "
            f"{road.destination}"
        )

        self.state.location = road.destination

        self.state.time_used += road.minutes

        self.state.money_spent += road.cost

        print(
            f"   State updated → "
            f"{self.state.location}"
        )

    # ========================================================
    # RE-PLANNING
    # ========================================================

    def replan(self):

        print("\n🔄 RE-PLANNING")
        print(
            "   Environment changed."
        )

        print(
            "   AI is generating a new plan "
            "from the current state..."
        )

        self.plan = self.plan_route()

        if self.plan is not None:
            self.show_plan(self.plan)

    # ========================================================
    # MAIN AGENT LOOP
    # ========================================================

    def run(self, events=None):

        events = events or {}

        print("\n" + "=" * 60)
        print("🤖 SMART COMMUTE AI AGENT")
        print("=" * 60)

        print(
            f"Goal      : {self.goal}"
        )

        print(
            f"Deadline  : {self.deadline} minutes"
        )

        print(
            f"Budget    : {self.budget:.2f} AZN"
        )

        print(
            f"Strategy  : {self.strategy}"
        )

        # ----------------------------------------------------
        # INITIAL OBSERVATION
        # ----------------------------------------------------

        self.observe()

        # ----------------------------------------------------
        # INITIAL PLANNING
        # ----------------------------------------------------

        self.plan = self.plan_route()

        if self.plan is None:
            print(
                "\n❌ Mission failed."
                "\nNo valid plan satisfies the constraints."
            )
            return

        self.show_plan(self.plan)

        # ----------------------------------------------------
        # AGENT LOOP
        # ----------------------------------------------------

        while not self.goal_reached():

            if not self.plan:

                self.replan()

                if not self.plan:
                    print(
                        "\n❌ Agent cannot continue."
                    )
                    return

            # Select next action
            next_action = self.plan.pop(0)

            # Execute action
            self.execute_action(next_action)

            # Observe new state
            self.observe()

            # ------------------------------------------------
            # ENVIRONMENT EVENT
            # ------------------------------------------------

            if (
                self.state.location in events
                and not self.goal_reached()
            ):

                closed_mode = events[
                    self.state.location
                ]

                print(
                    "\n🚨 ENVIRONMENT EVENT"
                )

                print(
                    f"   {closed_mode.upper()} "
                    f"has become unavailable!"
                )

                self.environment.close_mode(
                    closed_mode
                )

                # Re-plan
                self.replan()

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        print("\n" + "=" * 60)

        print("🎯 GOAL REACHED")

        print(
            f"   Destination : {self.state.location}"
        )

        print(
            f"   Total time  : {self.state.time_used} min"
        )

        print(
            f"   Total cost  : "
            f"{self.state.money_spent:.2f} AZN"
        )

        print(
            f"   Time limit  : "
            f"{self.deadline} min"
        )

        print(
            f"   Budget      : "
            f"{self.budget:.2f} AZN"
        )

        print("=" * 60)


# ============================================================
# 4. RUN AI EXPERIMENTS
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # EXPERIMENT 1
    # Fastest strategy
    # --------------------------------------------------------

    environment = CommuteEnvironment()

    agent = SmartCommuteAgent(
        environment=environment,
        start="Home",
        goal="University",
        deadline=70,
        budget=15,
        strategy="fastest"
    )

    agent.run()


    # --------------------------------------------------------
    # EXPERIMENT 2
    # Cheapest strategy
    # --------------------------------------------------------

    environment = CommuteEnvironment()

    agent = SmartCommuteAgent(
        environment=environment,
        start="Home",
        goal="University",
        deadline=70,
        budget=15,
        strategy="cheapest"
    )

    agent.run()


    # --------------------------------------------------------
    # EXPERIMENT 3
    # Balanced AI strategy
    # --------------------------------------------------------

    environment = CommuteEnvironment()

    agent = SmartCommuteAgent(
        environment=environment,
        start="Home",
        goal="University",
        deadline=70,
        budget=5,
        strategy="balanced"
    )

    agent.run()


    # --------------------------------------------------------
    # EXPERIMENT 4
    # Dynamic environment + RE-PLANNING
    # --------------------------------------------------------

    environment = CommuteEnvironment()

    agent = SmartCommuteAgent(
        environment=environment,
        start="Home",
        goal="University",
        deadline=70,
        budget=5,
        strategy="fastest"
    )

    agent.run(
        events={
            "Metro A": "metro"
        }
    )


    # --------------------------------------------------------
    # EXPERIMENT 5
    # Impossible mission
    # --------------------------------------------------------

    environment = CommuteEnvironment()

    agent = SmartCommuteAgent(
        environment=environment,
        start="Home",
        goal="University",
        deadline=20,
        budget=1,
        strategy="fastest"
    )

    agent.run()
