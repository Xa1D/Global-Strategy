from ai import AI
from player import Player
from testing_classes import TestTerritory, TestMap

class GameTests:
    def connect(self, a, b):
        a.adjacent.append(b.name)
        b.adjacent.append(a.name)

    def conquer(self, player, territory):
        player.territories.append(territory)
        territory.owner = player

    def check(self, name, expected, observed):
        passed = False
        if expected == observed:
            passed = True
        print(f"\n{name}")
        print(f"Expected: {expected}, Observed: {observed}")
        text = "Pass" if passed else "Fail"
        print(text)

    def test_BFS(self):
        a, b, c, d, e, f = [TestTerritory(name) for name in "ABCDEF"]
        world = TestMap([a, b, c, d, e, f])
        for t1, t2 in [(a, b), (b, d), (a, c), (c, e), (e, d)]:
            self.connect(t1, t2)
        ai = AI(a, "balanced")
        path1 = ai.search(a, d, world)
        path2 = ai.search(a, a, world)
        path3 = ai.search(a, f, world)
        self.check("BFS shortest route", ["A", "B", "D"], [territory.name for territory in path1])
        self.check("BFS same start and target", ["A"], [territory.name for territory in path2])
        self.check("BFS unreachable target", None, path3)
        b.units["artillery"] = 100
        a.units["infantry"] = 100
        self.check("Target selection", ["B"], [territory.name for territory in ai.choose_targets(world, 1)])

    def test_scoring(self):
        a, b = TestTerritory("A", 20), TestTerritory("B", 20)
        ai = AI(a, "balanced")
        scorer = ai.scorer
        for units, expected in [(10, 0), (20, 0), (30, 0.5), (40, 1), (50, 1)]:
            a.units["infantry"] = units
            count_ratio_score = scorer.count_ratio_score(a, b)
            self.check(f"Count ratios: {units} vs 20", expected, count_ratio_score)
        self.check("Path bonus", (0.15, 0),(scorer.path_bonus(a, {"A"}), scorer.path_bonus(a, {"B"})))
        a, b, c, d = [TestTerritory(name, units) for name, units in [("A", 15), ("B", 10), ("C", 15), ("D", 5)]]
        ai, enemy = AI(a, "balanced"), Player(b)
        self.conquer(ai, c)
        self.conquer(enemy, d)      #ai owns a and c, enemy owns b and d
        #ai has 15 units in 2 territories, enemy has 10 and 5 units
        self.connect(a,b)
        self.connect(a,c)
        self.connect(a,d)
        #Calculates count, value connectivity and threat score using parameters to generate final score
        #count score - 15/10 - 1 = 0.5
        #value score - same as above since only infantry
        #connectivity score - 15/15 = 1
        #threat score - 1 - (10 + 5) / 15 = 0
        self.check("Territory scoring", 0.5, ai.scorer.score_territory(a, b, TestMap([a, b, c, d]), enemy))
        #final score should be 0.5 once weights are applied 

    def run(self):
        try:
            self.test_BFS()
            self.test_scoring()
        except Exception as error:
            print(f"ERROR: {error}")

tests = GameTests()
tests.run()