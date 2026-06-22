import math


def cosine(left: list[float], right: list[float]) -> float:
    total = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for left_value, right_value in zip(left, right, strict=False):
        total += left_value * right_value
        left_norm += left_value * left_value
        right_norm += right_value * right_value
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return total / (math.sqrt(left_norm) * math.sqrt(right_norm))
