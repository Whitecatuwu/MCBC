from dataclasses import dataclass, field


@dataclass
class Operation:
    delete: set[str] = field(default_factory=set)
    rename: set[tuple[str, str]] = field(default_factory=set)
    modify: set[tuple[str, str]] = field(default_factory=set)
    apply: set[tuple[str, str]] = field(default_factory=set)
