from __future__ import annotations

import math
from typing import Iterable


EPSILON = 1e-9
Vector3 = tuple[float, float, float]
Quaternion = tuple[float, float, float, float]


def _vector(value: Iterable[float]) -> Vector3:
    values = tuple(float(item) for item in value)
    if len(values) != 3 or not all(math.isfinite(item) for item in values):
        raise ValueError("expected a finite three-dimensional vector")
    return values  # type: ignore[return-value]


def add(a: Iterable[float], b: Iterable[float]) -> Vector3:
    av, bv = _vector(a), _vector(b)
    return tuple(av[i] + bv[i] for i in range(3))  # type: ignore[return-value]


def subtract(a: Iterable[float], b: Iterable[float]) -> Vector3:
    av, bv = _vector(a), _vector(b)
    return tuple(av[i] - bv[i] for i in range(3))  # type: ignore[return-value]


def scale(value: Iterable[float], factor: float) -> Vector3:
    vector = _vector(value)
    if not math.isfinite(factor):
        raise ValueError("scale factor must be finite")
    return tuple(item * factor for item in vector)  # type: ignore[return-value]


def dot(a: Iterable[float], b: Iterable[float]) -> float:
    av, bv = _vector(a), _vector(b)
    return sum(av[i] * bv[i] for i in range(3))


def cross(a: Iterable[float], b: Iterable[float]) -> Vector3:
    av, bv = _vector(a), _vector(b)
    return (
        av[1] * bv[2] - av[2] * bv[1],
        av[2] * bv[0] - av[0] * bv[2],
        av[0] * bv[1] - av[1] * bv[0],
    )


def norm(value: Iterable[float]) -> float:
    vector = _vector(value)
    return math.sqrt(dot(vector, vector))


def normalize(value: Iterable[float]) -> Vector3:
    vector = _vector(value)
    length = norm(vector)
    if length <= EPSILON:
        raise ValueError("cannot normalize a zero-length vector")
    return scale(vector, 1.0 / length)


def distance(a: Iterable[float], b: Iterable[float]) -> float:
    return norm(subtract(a, b))


def clamp(value: float, lower: float, upper: float) -> float:
    if lower > upper:
        raise ValueError("lower bound must not exceed upper bound")
    return max(lower, min(upper, float(value)))


def angle_between(a: Iterable[float], b: Iterable[float]) -> float:
    return math.degrees(math.acos(clamp(dot(normalize(a), normalize(b)), -1.0, 1.0)))


def is_finite(value: Iterable[float]) -> bool:
    try:
        _vector(value)
    except (TypeError, ValueError):
        return False
    return True


def triangle_normal(a: Iterable[float], b: Iterable[float], c: Iterable[float]) -> Vector3:
    return normalize(cross(subtract(b, a), subtract(c, a)))


def orthonormal_basis(normal: Iterable[float], reference: Iterable[float] = (0, 0, 1)) -> tuple[Vector3, Vector3, Vector3]:
    z_axis = normalize(normal)
    ref = normalize(reference)
    if abs(dot(z_axis, ref)) > 0.98:
        ref = (1.0, 0.0, 0.0)
    x_axis = normalize(cross(ref, z_axis))
    y_axis = normalize(cross(z_axis, x_axis))
    return x_axis, y_axis, z_axis


def matrix_vector_transform(matrix: Iterable[Iterable[float]], vector: Iterable[float]) -> Vector3:
    rows = tuple(_vector(row) for row in matrix)
    if len(rows) != 3:
        raise ValueError("expected a finite 3x3 matrix")
    value = _vector(vector)
    return tuple(dot(row, value) for row in rows)  # type: ignore[return-value]


def quaternion_normalize(value: Iterable[float]) -> Quaternion:
    items = tuple(float(item) for item in value)
    if len(items) != 4 or not all(math.isfinite(item) for item in items):
        raise ValueError("expected a finite quaternion")
    length = math.sqrt(sum(item * item for item in items))
    if length <= EPSILON:
        raise ValueError("cannot normalize a zero quaternion")
    return tuple(item / length for item in items)  # type: ignore[return-value]


def rotation_matrix_to_quaternion(matrix: Iterable[Iterable[float]]) -> Quaternion:
    rows = tuple(_vector(row) for row in matrix)
    if len(rows) != 3:
        raise ValueError("expected a finite 3x3 rotation matrix")
    m00, m01, m02 = rows[0]
    m10, m11, m12 = rows[1]
    m20, m21, m22 = rows[2]
    trace = m00 + m11 + m22
    if trace > 0:
        s = math.sqrt(trace + 1.0) * 2
        result = (0.25 * s, (m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s)
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2
        result = ((m21 - m12) / s, 0.25 * s, (m01 + m10) / s, (m02 + m20) / s)
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2
        result = ((m02 - m20) / s, (m01 + m10) / s, 0.25 * s, (m12 + m21) / s)
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2
        result = ((m10 - m01) / s, (m02 + m20) / s, (m12 + m21) / s, 0.25 * s)
    return quaternion_normalize(result)


def quaternion_angular_distance(a: Iterable[float], b: Iterable[float]) -> float:
    qa, qb = quaternion_normalize(a), quaternion_normalize(b)
    similarity = abs(sum(qa[i] * qb[i] for i in range(4)))
    return math.degrees(2.0 * math.acos(clamp(similarity, -1.0, 1.0)))
