"""
Robot Tozsoran simulyasiyası (Roomba tipli)

Real həyat ssenarisi:
- Otaq şəbəkə (grid) kimi təsvir olunur.
- Otaqda mebel (maneə) və müxtəlif səviyyədə çirk var.
- Robotun batareyası və tozqabı məhduddur.
- Batareya azalanda və ya tozqabı dolanda robot dok stansiyasına qayıdır.
- Robot hər dəfə ən yaxın çirkə gedir (BFS axtarışı ilə).
"""

from collections import deque
import random


class Room:
    """Otaq: ölçü, maneələr, dok stansiyası və çirk xəritəsi."""

    def __init__(self, rows, cols, obstacles, dock):
        self.rows = rows
        self.cols = cols
        self.obstacles = set(obstacles)   # mebel olan xanalar
        self.dock = dock                  # şarj stansiyasının yeri
        self.dirt = {}                    # {(sətir, sütun): çirk səviyyəsi 1-3}

    def add_random_dirt(self, count, seed=1):
        rnd = random.Random(seed)         # seed: hər dəfə eyni nəticə üçün
        while len(self.dirt) < count:
            cell = (rnd.randrange(self.rows), rnd.randrange(self.cols))
            if cell not in self.obstacles and cell != self.dock:
                self.dirt[cell] = rnd.randint(1, 3)

    def is_free(self, cell):
        r, c = cell
        inside = 0 <= r < self.rows and 0 <= c < self.cols
        return inside and cell not in self.obstacles

    def show(self, robot_pos=None):
        """Otağı mətn şəklində çəkir: R=robot, D=dok, #=mebel, rəqəm=çirk."""
        for r in range(self.rows):
            line = ""
            for c in range(self.cols):
                cell = (r, c)
                if cell == robot_pos:
                    line += " R "
                elif cell == self.dock:
                    line += " D "
                elif cell in self.obstacles:
                    line += " # "
                elif cell in self.dirt:
                    line += f" {self.dirt[cell]} "
                else:
                    line += " . "
            print(line)
        print()


class RobotVacuum:
    """Robot tozsoran: batareya, tozqabı və təmizləmə məntiqi."""

    MOVE_COST = 1    # 1 addım = 1 batareya
    CLEAN_COST = 2   # 1 çirk səviyyəsini təmizləmək = 2 batareya

    def __init__(self, room, battery=40, bin_capacity=8):
        self.room = room
        self.pos = room.dock
        self.max_battery = battery
        self.battery = battery
        self.bin_capacity = bin_capacity
        self.bin = 0
        # Statistika
        self.steps = 0
        self.cleaned_cells = 0
        self.recharges = 0

    # ---------- Yol tapma (BFS) ----------
    def find_path(self, start, goal_test):
        """Start-dan şərti ödəyən ən yaxın xanaya ən qısa yolu qaytarır.
        Yol tapılmasa None qaytarır."""
        if goal_test(start):
            return []
        queue = deque([start])
        came_from = {start: None}         # hər xanaya hardan gəldiyimizi saxlayır
        while queue:
            current = queue.popleft()
            r, c = current
            for nxt in [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]:
                if self.room.is_free(nxt) and nxt not in came_from:
                    came_from[nxt] = current
                    if goal_test(nxt):
                        # Yolu geriyə doğru bərpa edirik
                        path = []
                        while nxt != start:
                            path.append(nxt)
                            nxt = came_from[nxt]
                        path.reverse()
                        return path
                    queue.append(nxt)
        return None

    # ---------- Hərəkət və təmizləmə ----------
    def follow(self, path):
        for cell in path:
            self.pos = cell
            self.battery -= self.MOVE_COST
            self.steps += 1

    def clean_here(self):
        level = self.room.dirt.pop(self.pos)
        self.bin += level
        self.battery -= self.CLEAN_COST * level
        self.cleaned_cells += 1
        print(f"  Təmizləndi {self.pos} (çirk={level}) | batareya={self.battery}, tozqabı={self.bin}/{self.bin_capacity}")

    def go_to_dock(self, reason):
        print(f"-> Dok stansiyasına qayıdır ({reason})")
        path = self.find_path(self.pos, lambda c: c == self.room.dock)
        self.follow(path)
        self.battery = self.max_battery   # şarj olur
        self.bin = 0                      # tozqabı boşaldılır
        self.recharges += 1
        print("   Şarj olundu, tozqabı boşaldıldı.")

    # ---------- Əsas dövr ----------
    def run(self):
        while self.room.dirt:
            # 1) Tozqabı doludursa
            if self.bin >= self.bin_capacity:
                self.go_to_dock("tozqabı dolub")
                continue

            # 2) Ən yaxın çirki tap
            path = self.find_path(self.pos, lambda c: c in self.room.dirt)
            if path is None:
                print("Qalan çirkə çatmaq mümkün deyil (maneələr bağlayır).")
                break

            # 3) Batareya çatacaq? (çirkə get + təmizlə + dok-a qayıt)
            target = path[-1]
            back = self.find_path(target, lambda c: c == self.room.dock)
            need = (len(path) + len(back)) * self.MOVE_COST \
                   + self.CLEAN_COST * self.room.dirt[target]
            if need > self.battery:
                if self.pos == self.room.dock:
                    print("Batareya tam dolu olsa belə çatmır, dayandı.")
                    break
                self.go_to_dock("batareya azdır")
                continue

            # 4) Get və təmizlə
            self.follow(path)
            self.clean_here()

        # Iş bitəndə dok-a qayıt
        if self.pos != self.room.dock:
            self.go_to_dock("iş bitdi")

    def report(self):
        print("=== HESABAT ===")
        print(f"Təmizlənən xana sayı : {self.cleaned_cells}")
        print(f"Ümumi addım sayı     : {self.steps}")
        print(f"Şarj olma sayı       : {self.recharges}")
        print(f"Qalan çirk           : {len(self.room.dirt)}")


if __name__ == "__main__":
    # 6x8 otaq, bir neçə mebel (divan, masa), dok sol yuxarı küncdə
    room = Room(
        rows=6, cols=8,
        obstacles=[(1, 3), (2, 3), (3, 3), (4, 5), (4, 6)],
        dock=(0, 0),
    )
    room.add_random_dirt(count=10)

    print("Başlanğıc vəziyyət:")
    room.show(robot_pos=room.dock)

    robot = RobotVacuum(room, battery=40, bin_capacity=8)
    robot.run()

    print("\nSon vəziyyət:")
    room.show(robot_pos=robot.pos)
    robot.report()
