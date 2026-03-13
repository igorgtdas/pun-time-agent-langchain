from dataclasses import dataclass, field


@dataclass
class Context:
    """Custom runtime context schema."""
    user_id: str
    tool_failures: dict[str, str] = field(default_factory=dict)
