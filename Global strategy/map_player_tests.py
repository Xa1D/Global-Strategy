from map import Map as GameMap
from player import Player
from testing_classes import TestMap, TestTerritory, check

def connect(a, b):
    a.adjacent.append(b.name)
    b.adjacent.append(a.name)

def claim(player, territory):
    player.territories.append(territory)
    territory.owner = player

def test_map_connectivity():
    for filename in ("europe_coordinates.json", "asia_coordinates.json", "africa_coordinates.json"):
        world = GameMap(filename)
        territories = list(world.territories.values())
        reciprocal = all(name in world.territories and territory.name in world.territories[name].adjacent for territory in territories for name in territory.adjacent)
        visited, queue = {territories[0].name}, [territories[0]]
        while queue:
            current = queue.pop(0)
            for name in current.adjacent:
                if name not in visited:
                    visited.add(name)
                    queue.append(world.territories[name])
        check(f"{world.map}: adjacency is double-sided", "4.2", True, reciprocal)
        check(f"{world.map}: all territories are reachable", "4.2", len(territories), len(visited))

def test_player_actions():
    source = TestTerritory("Source", infantry=10, tank=4, artillery=2)
    target = TestTerritory("Target")
    player = Player(source)
    claim(player, target)
    connect(source, target)

    currency = player.currency
    player.buy_units(source, "infantry", 2)
    check("Purchase changes currency and unit count", "1.5 / 1.6", (currency - 10, 12),
          (player.currency, source.units["infantry"]))

    total_before = source.total_units() + target.total_units()
    moved = player.move_units(source, target, 3, 1, 1)
    check("Valid move preserves total unit count", "4.4 / 4.5", True,
          moved and source.total_units() + target.total_units() == total_before)

    before = (source.total_units(), target.total_units())
    rejected = not player.move_units(source, target, 999, 0, 0)
    check("Move rejects unavailable units without changing counts", "4.5 / 8.1", True,
          rejected and before == (source.total_units(), target.total_units()))


if __name__ == "__main__":
    test_map_connectivity()
    test_player_actions()
