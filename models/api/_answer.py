
from dataclasses import dataclass, field

@dataclass
class ApiAnswer:
    token_status: str = "success"
    status:str = ""
    error: int = 0
    status_code: int = 200
    status_description:str = ""
    data: dict = field(default_factory = lambda: {})