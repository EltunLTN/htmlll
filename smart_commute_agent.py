"""
Smart Commute Agent - a Goal-Based Agent for a real-life situation

Situation:
    You are at home and must reach the university on time without
    spending too much money. You can walk, take a bus, take the metro,
    or call a taxi.

What makes this a goal-based agent?
    1. GOAL        : be at the University before the deadline, within budget.
    2. STATE       : current location, minutes used, money spent.
    3. PLANNING    : before moving, the agent imagines many possible routes
                     ("what will happen if I take this road?") and picks the
                     best one according to a strategy.
    4. RE-PLANNING : if something changes (e.g. the metro closes), the agent
                     makes a NEW plan from where it currently is.
"""

from collections import namedtuple

# One road between two places.
Road = namedtuple("Road", ["to", "mode", "minutes", "cost"])


# ---------------------------------------------------------------------------
# 1. The world (map of the city)
# ---------------------------------------------------------------------------
def build_city():
    city = {}

    def connect(a, b, mode, minutes, cost):
        """Roads work in both directions."""
        city.setdefault(a, []).append(Road(b, mode, minutes, cost))
        city.setdefault(b, []).append(Road(a, mode, minutes, cost))

    connect("Home", "Bus Stop", "walk", 5, 0.0)
    connect("Home", "Metro A", "walk", 15, 0.0)
    connect("Home", "University", "taxi", 25, 12.0)

    connect("Bus Stop", "Metro A", "bus", 10, 0.5)
    connect("Bus Stop", "University", "bus", 45, 0.6)

    connect("Metro A", "Metro B", "metro", 12, 0.5)
    connect("Metro A", "University", "taxi", 15, 8.0)

    connect("Metro B", "University", "walk", 10, 0.0)
    connect("Metro B", "University", "taxi", 4, 3.0)

    return city


# ---------------------------------------------------------------------------
# 2. The agent
# ---------------------------------------------------------------------------
class CommuteAgent:
    def __init__(self, city, start, goal, deadline, budget, strategy):
        self.city = city
        self.location = start        # current state
        self.goal = goal             # the goal
        self.deadline = deadline     # max total minutes allowed
        self.budget = budget         # max total money allowed
        self.strategy = strategy     # "fastest", "cheapest" or "balanced"
        self.time_used = 0
        self.money_spent = 0.0
        self.blocked_modes = set()   # e.g. {"metro"} when the metro is closed

    # --- goal test --------------------------------------------------------
    def is_goal(self, location):
        return location == self.goal

    # --- how good is a route? (lower score = better) ----------------------
    def score(self, minutes, cost):
        if self.strategy == "fastest":
            return minutes
        if self.strategy == "cheapest":
            return cost
        return minutes + 5 * cost    # balanced: 1 AZN is worth 5 minutes

    # --- planning: imagine all possible futures, keep the best ------------
    def make_plan(self):
        """
        Explores routes WITHOUT moving. Every route that breaks the deadline
        or the budget is thrown away. Returns the best list of Roads,
        or None if the goal cannot be reached.
        """
        best_plan, best_score = None, None

        # Each item: (place, roads taken so far, minutes used, money spent)
        stack = [(self.location, [], self.time_used, self.money_spent)]

        while stack:
            place, roads, minutes, money = stack.pop()

            if self.is_goal(place):
                s = self.score(minutes - self.time_used, money - self.money_spent)
                if best_score is None or s < best_score:
                    best_plan, best_score = roads, s
                continue

            for road in self.city[place]:
                if road.mode in self.blocked_modes:
                    continue                                  # road unusable

                new_minutes = minutes + road.minutes
                new_money = money + road.cost
                if new_minutes > self.deadline or new_money > self.budget:
                    continue                                  # constraint broken

                # Do not walk in circles within the same route.
                places_in_route = {self.location} | {r.to for r in roads}
                if road.to in places_in_route:
                    continue

                stack.append((road.to, roads + [road], new_minutes, new_money))

        return best_plan

    # --- acting -----------------------------------------------------------
    def go(self, road):
        self.location = road.to
        self.time_used += road.minutes
        self.money_spent += road.cost

    def show_plan(self, plan):
        total_min = sum(r.minutes for r in plan)
        total_cost = sum(r.cost for r in plan)
        print(f"  New plan: {total_min} more min, {total_cost:.1f} AZN more")
        place = self.location
        for r in plan:
            print(f"    {place} --{r.mode}--> {r.to} ({r.minutes} min, {r.cost:.1f} AZN)")
            place = r.to

    def run(self, events=None):
        """
        events: {place: mode_that_closes_when_agent_arrives_there}
        Example: {"Metro A": "metro"} -> metro closes when we reach Metro A.
        """
        events = events or {}
        print(f"\n=== Strategy: {self.strategy} | deadline: {self.deadline} min "
              f"| budget: {self.budget} AZN ===")

        plan = self.make_plan()
        if plan is None:
            print("  No plan can satisfy the deadline and the budget!")
            return
        self.show_plan(plan)

        while not self.is_goal(self.location):
            road = plan.pop(0)
            self.go(road)
            print(f"  -> Moved to {self.location} by {road.mode} "
                  f"[time {self.time_used} min, spent {self.money_spent:.1f} AZN]")

            # Something unexpected happens in the world.
            if self.location in events and not self.is_goal(self.location):
                closed = events[self.location]
                self.blocked_modes.add(closed)
                print(f"  !! News: the {closed} is closed! Re-planning...")
                plan = self.make_plan()
                if plan is None:
                    print("  No new plan is possible. The goal cannot be reached.")
                    return
                self.show_plan(plan)

        print(f"  GOAL REACHED: {self.goal} in {self.time_used} min, "
              f"{self.money_spent:.1f} AZN")


# ---------------------------------------------------------------------------
# 3. Experiments
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    city = build_city()

    # Same goal, different strategies -> different plans.
    for strategy in ["fastest", "cheapest", "balanced"]:
        CommuteAgent(city, "Home", "University",
                     deadline=70, budget=15, strategy=strategy).run()

    # Re-planning: the metro closes when the agent arrives at Metro A.
    CommuteAgent(city, "Home", "University",
                 deadline=70, budget=5, strategy="fastest").run(
        events={"Metro A": "metro"}
    )

    # Impossible goal: very tight deadline and a very small budget.
    CommuteAgent(city, "Home", "University",
                 deadline=20, budget=1, strategy="fastest").run()
