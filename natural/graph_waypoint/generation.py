#!/usr/bin/env python3
import os
import random
from collections import deque

# ── CONFIG ───────────────────────────────────────────────────────────────────────
module_dir   = "./natural/graph/"
os.makedirs(module_dir, exist_ok=True)

natural_path = os.path.join(module_dir, "natural.txt")

NUM_INSTANCES = 30
MIN_NODES, MAX_NODES = 21, 30 # 5, 10
EDGE_PROB     = 0.4  # p for Erdos–Rényi

# planetary amenity pool (15 items)
amenity_pool_nat = [
    "fueling port",
    "science station",
    "repair bay",
    "trading post",
    "medical bay",
    "communications hub",
    "hydroponics lab",
    "research outpost",
    "docking bay",
    "navigation beacon",
    "escape pod bay",
    "asteroid mining station",
    "quantum relay",
    "warp core injector",
    "stellar observatory"
]

# planet names (50 total)
planets = [
    "Aegis", "Arcadia", "Bellatrix", "Boreas", "Cetus",
    "Corvus", "Deneb", "Draco", "Elara", "Elysia",
    "Fomalhaut", "Fenrir", "Ganymede", "Gaia", "Helios",
    "Hyperion", "Icarus", "Io", "Janus", "Juno",
    "Kelvin", "Krypton", "Levania", "Luna", "Midas",
    "Miranda", "Nereus", "Nova", "Oberon", "Orion",
    "Phoebe", "Pulsar", "Quasar", "Rigel", "Rhea",
    "Selene", "Styx", "Triton", "Titan", "Umbra",
    "Umbriel", "Vega", "Winona", "Wraith", "Xandar",
    "Xenon", "Ymir", "Yavin", "Zephyr", "Zebes"
]

# ── HELPERS ──────────────────────────────────────────────────────────────────────
def generate_connected_er_graph(nodes, p):
    """Build a connected ER graph on `nodes` with edge‐prob `p`."""
    while True:
        edges = []
        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                if random.random() < p:
                    edges.append((nodes[i], nodes[j]))
        # check connectivity via BFS
        adj = {n: [] for n in nodes}
        for u, v in edges:
            adj[u].append(v)
            adj[v].append(u)
        visited = set()
        queue = deque([nodes[0]])
        while queue:
            u = queue.popleft()
            if u in visited:
                continue
            visited.add(u)
            for nbr in adj[u]:
                if nbr not in visited:
                    queue.append(nbr)
        if len(visited) == len(nodes):
            return edges

def dfs_full(adj, source):
    """Return DFS order (sorted‐neighbor first) starting at source."""
    visited, order = set(), []
    def dfs(u):
        visited.add(u)
        order.append(u)
        for v in sorted(adj[u]):
            if v not in visited:
                dfs(v)
    dfs(source)
    return order

def bfs_path(adj, start, end):
    """Return one shortest path from start to end via BFS."""
    parent = {start: None}
    queue = deque([start])
    while queue:
        u = queue.popleft()
        if u == end:
            break
        for v in adj[u]:
            if v not in parent:
                parent[v] = u
                queue.append(v)
    # reconstruct
    path = []
    cur = end
    while cur is not None:
        path.append(cur)
        cur = parent.get(cur)
    return list(reversed(path))

def write_block(f, **kwargs):
    """Write each key: value pair on its own line, then a blank line."""
    for k, v in kwargs.items():
        f.write(f"{k}: {v}\n")
    f.write("\n")


with open(natural_path, "w") as fl:
    for _ in range(NUM_INSTANCES):
        # 1) pick planets
        n = random.randint(MIN_NODES, MAX_NODES)
        nodes = random.sample(planets, n)

        # 2) generate a connected ER graph
        edges = generate_connected_er_graph(nodes, EDGE_PROB)

        # 3) assign amenities
        amenities = {
            p: random.sample(amenity_pool_nat, random.randint(1, 3))
            for p in nodes
        }

        # 4) build adjacency
        adj = {p: [] for p in nodes}
        for u, v in edges:
            adj[u].append(v)
            adj[v].append(u)

        # 5) choose start & target
        source, target = random.sample(nodes, 2)

        # 6) find a path from source to target (to ensure satisfiable waypoints)
        route = bfs_path(adj, source, target)

        # 7) pick required_amenities from those available along that route
        available = sorted({a for planet in route for a in amenities[planet]})
        num_req = min(len(available), random.randint(1, 3))
        required_amenities = random.sample(available, num_req)

        # 8) compute the full DFS traversal (for evaluation/truth)
        dfs_path = dfs_full(adj, source)

        # 9) write out the instance
        write_block(fl,
            nodes=nodes,
            edges=edges,
            amenities=amenities,
            required_amenities=required_amenities,
            source=source,
            target=target,
            dfs_path=dfs_path
        )
