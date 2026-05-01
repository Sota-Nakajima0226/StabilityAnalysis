from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class Moduli9d:
    id: int
    removed_nodes: Any
    a9: Any
    g9: str
    gauge_group: Any
    maximal_enhanced: Optional[int]
    cosmological_constant: Optional[int]
    is_critical_point: Optional[int]
    hessian: Any
    type: Optional[str]


@dataclass
class Moduli8d:
    id: int
    removed_nodes: Any
    moduli_9d_id: int
    delta: Any
    gauge_group: Any
    maximal_enhanced: Optional[int]
    cosmological_constant: Optional[int]
    is_critical_point: Optional[int]
    hessian: Any
    type: Optional[str]


@dataclass
class MasslessSolution9d:
    id: int
    moduli_9d_id: int
    element: Any


@dataclass
class Coset8d:
    id: int
    moduli_8d_id: int
    massless_solution_9d_id: int
    character: int


@dataclass
class JoinedModuli8d:
    id: int
    a9: Any
    g9: str
    delta: Any
