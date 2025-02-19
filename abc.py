from itertools import permutations

# Ma trận khoảng cách giữa các đỉnh (theo thứ tự A, B, C, D, E, F, G, H)
dist = [
    [0, 6, float('inf'), float('inf'), float('inf'), 5, 8, float('inf')],  # A
    [6, 0, 7, float('inf'), float('inf'), float('inf'), float('inf'), float('inf')],  # B
    [float('inf'), 7, 0, 9, float('inf'), float('inf'), float('inf'), float('inf')],  # C
    [float('inf'), float('inf'), 9, 0, float('inf'), float('inf'), 8, 10],  # D
    [float('inf'), float('inf'), float('inf'), float('inf'), 0, 9, 5, 5],  # E
    [5, float('inf'), float('inf'), float('inf'), 9, 0, 8, float('inf')],  # F
    [8, float('inf'), float('inf'), 8, 5, 8, 0, 6],  # G
    [float('inf'), float('inf'), float('inf'), 10, 5, float('inf'), 6, 0]   # H
]

cities = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

def calculate_distance(path):
    total = 0
    for i in range(len(path) - 1):
        total += dist[path[i]][path[i + 1]]
    total += dist[path[-1]][path[0]]  # Quay lại điểm xuất phát
    return total

min_distance = float('inf')
best_path = []

for perm in permutations(range(1, len(cities))):
    path = [0] + list(perm)
    distance = calculate_distance(path)
    if distance < min_distance:
        min_distance = distance
        best_path = path

best_path_named = [cities[i] for i in best_path]
print(f"Đường đi ngắn nhất: {' -> '.join(best_path_named)} -> {best_path_named[0]}")
print(f"Chi phí nhỏ nhất: {min_distance}")
