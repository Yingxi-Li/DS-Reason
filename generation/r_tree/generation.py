import math
import random
import matplotlib.pyplot as plt

class Node:
    """
    Basic R-tree node. Internal nodes hold child nodes; leaf nodes hold rectangle entries.
    """
    def __init__(self, children=None, entries=None):
        # entries: list of rectangles (xmin, xmax, ymin, ymax) for leaf nodes
        # children: list of Node for internal nodes
        self.entries = entries
        self.children = children
        self.is_leaf = entries is not None
        self.mbr = self._compute_mbr()

    def _compute_mbr(self):
        # Compute minimal bounding rectangle for this node
        rects = self.entries if self.is_leaf else [child.mbr for child in self.children]
        xmin = min(r[0] for r in rects)
        xmax = max(r[1] for r in rects)
        ymin = min(r[2] for r in rects)
        ymax = max(r[3] for r in rects)
        return (xmin, xmax, ymin, ymax)

class RTree:
    """
    Basic R-tree using STR bulk-loading for construction, with preorder traversal and visualization.
    """
    def __init__(self, max_entries=16):
        self.M = max_entries
        self.root = None

    def build(self, rectangles):
        """
        Build the R-tree from a list of rectangles [(xmin, xmax, ymin, ymax), ...].
        Uses a fixed STR bulk-loading strategy.
        """
        # Create leaf nodes
        leaf_nodes = self._bulk_load(rectangles, is_leaf=True)
        nodes = leaf_nodes
        # Build upper levels until root
        while len(nodes) > self.M:
            nodes = self._bulk_load(nodes, is_leaf=False)
        # Remaining nodes form the root
        self.root = nodes[0] if len(nodes) == 1 else Node(children=nodes)
        return self.root

    def _bulk_load(self, entries, is_leaf):
        """
        Bulk-load a level of the R-tree.
        entries: list of rectangles (if is_leaf) or list of Node.
        Returns: list of Node at this level.
        """
        N = len(entries)
        M = self.M
        node_count = math.ceil(N / M)
        S = math.ceil(math.sqrt(node_count))
        # Sort entries by x-center
        if is_leaf:
            sorted_list = sorted(entries, key=lambda r: (r[0] + r[1]) / 2)
        else:
            sorted_list = sorted(entries, key=lambda n: (n.mbr[0] + n.mbr[1]) / 2)
        slice_size = math.ceil(N / S)
        slices = [sorted_list[i*slice_size:(i+1)*slice_size] for i in range(S)]
        nodes = []
        for sl in slices:
            # Sort each slice by y-center
            if is_leaf:
                sl_sorted = sorted(sl, key=lambda r: (r[2] + r[3]) / 2)
            else:
                sl_sorted = sorted(sl, key=lambda n: (n.mbr[2] + n.mbr[3]) / 2)
            for i in range(0, len(sl_sorted), M):
                chunk = sl_sorted[i:i+M]
                node = Node(entries=chunk) if is_leaf else Node(children=chunk)
                nodes.append(node)
        return nodes

    def preorder(self):
        """
        Generator for preorder traversal: yields each node (with its MBR) then recurses children.
        """
        if self.root is None:
            return
        def _traverse(node):
            yield node
            if not node.is_leaf:
                for child in node.children:
                    yield from _traverse(child)
        yield from _traverse(self.root)

    def visualize(self, show=True, ax=None):
        """
        Plot the R-tree node boundaries. Deeper levels are shown in different colors.
        """
        if self.root is None:
            raise ValueError("Tree is empty. Build it first.")
        # Prepare plot
        own_fig = False
        if ax is None:
            fig, ax = plt.subplots()
            own_fig = True
        # Recursive draw
        def _draw(node, depth=0):
            xmin, xmax, ymin, ymax = node.mbr
            rect = plt.Rectangle((xmin, ymin), xmax-xmin, ymax-ymin,
                                 fill=False, linestyle='-', linewidth=1,
                                 edgecolor=f'C{depth % 10}')
            ax.add_patch(rect)
            # Leaf: also draw entries
            if node.is_leaf:
                for r in node.entries:
                    rxmin, rxmax, rymin, rymax = r
                    subrect = plt.Rectangle((rxmin, rymin), rxmax-rxmin, rymax-rymin,
                                             fill=False, linestyle='--', linewidth=0.5,
                                             edgecolor=f'C{depth % 10}')
                    ax.add_patch(subrect)
            else:
                for child in node.children:
                    _draw(child, depth+1)
        _draw(self.root, depth=0)
        ax.set_aspect('equal')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        if own_fig and show:
            plt.savefig('r_tree_visualization.png')
            plt.show()
        return ax


def generate_random_balanced_rectangles(n, x_range=(0, 1), y_range=(0, 1), fill_ratio=0.8, jitter=0.3):
    """
    Generate n rectangles arranged on a grid with random jitter to achieve balance while varying data.
    - fill_ratio controls rectangle size relative to cell.
    - jitter controls max displacement of rectangle center (fraction of half cell size).
    Returns list of (xmin, xmax, ymin, ymax).
    """
    x_min, x_max = x_range
    y_min, y_max = y_range
    rows = math.ceil(math.sqrt(n))
    cols = math.ceil(n / rows)
    cell_w = (x_max - x_min) / cols
    cell_h = (y_max - y_min) / rows
    rect_w = cell_w * fill_ratio
    rect_h = cell_h * fill_ratio
    max_jx = cell_w * jitter / 2
    max_jy = cell_h * jitter / 2
    rects = []
    for i in range(n):
        r = i // cols
        c = i % cols
        # Base center
        cx = x_min + (c + 0.5) * cell_w
        cy = y_min + (r + 0.5) * cell_h
        # Random jitter
        cx += random.uniform(-max_jx, max_jx)
        cy += random.uniform(-max_jy, max_jy)
        xmin = round(cx - rect_w / 2, 2)
        xmax = round(cx + rect_w / 2, 2)
        ymin = round(cy - rect_h / 2, 2)
        ymax = round(cy + rect_h / 2, 2)
        rects.append((xmin, xmax, ymin, ymax))
    return rects

if __name__ == '__main__':
    
    path = "generation/r_tree"
    
    for mode in ["easy"]: # "easy", "medium", "hard"
        all_points = []
        all_traversals = []
        with open(f"{path}/construction/rt_construction_{mode}.txt", "w") as f:
            if mode == "easy":
                M = 3
                min_size = 5
                max_size = 10
            elif mode == "medium":
                M = 5
                min_size = 15
                max_size = 20
            else:
                M = 7
                min_size = 21
                max_size = 30
                
            for k in range(30):
                size = max_size
                points = generate_random_balanced_rectangles(10, x_range=(0, 100), y_range=(0, 100))
                tree = RTree(max_entries=M)
                tree.build(points)
                traversal = [node.mbr for node in tree.preorder()]
                
                f.write(f"Tree {k}, M = {tree.M}\n")
                f.write(f"Points: {[list(pt) for pt in points]}\n")
                f.write(f"Traversal: {[list(pt) for pt in traversal]}\n")
    
    # data = generate_random_balanced_rectangles(10, x_range=(0, 100), y_range=(0, 100))
    # tree = RTree(max_entries=3)
    # tree.build(data)
    
    # print(f"Preorder traversal of the R-tree: {[node.mbr for node in tree.preorder()]}")
    # tree.visualize()
