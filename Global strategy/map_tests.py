from map import Map 
from testing_classes import test
 
def connect(a, b):
    a.adjacent.append(b.name)
    b.adjacent.append(a.name)
 
def claim(player, territory):
    player.territories.append(territory)
    territory.owner = player
 
class MapTests:
    def __init__(self, file):
        self.file = file  
 
    def test_map_connectivity(self):
        for filename in ("europe_coordinates.json", "asia_coordinates.json", "africa_coordinates.json"):
            world = Map(filename)
            territories = list(world.territories.values())
            double_link = all(name in world.territories and territory.name in world.territories[name].adjacent for territory in territories for name in territory.adjacent)
            visited, queue = {territories[0].name}, [territories[0]]
            while queue:
                current = queue.pop(0)
                for name in current.adjacent:
                    if name not in visited:
                        visited.add(name)
                        queue.append(world.territories[name])
            test(self.file, f"{world.map}: adjacency is double-sided", "4.2", True, double_link)
            test(self.file, f"{world.map}: all territories are reachable", "4.2", len(territories), len(visited))
 
    def run(self):
        try:
            self.test_map_connectivity()
        except Exception as error:  
            self.file.write(f"\n{test.__name__} ERROR: {type(error).__name__}: {error}\n")
 
if __name__ == "__main__":
    with open("map_tests_results.txt", "w") as file:
        MapTests(file).run()