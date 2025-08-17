from pydantic import BaseModel
from typing import Optional

class Users(BaseModel):
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    easy_solved: int = 0
    medium_solved: int = 0
    hard_solved: int = 0

    # These are not used, the points and total solved are calculated in the insertion process, just leave alone
    @property
    def total_solved(self) -> int:
        return self.easy_solved + self.medium_solved + self.hard_solved
    
    @property
    def points(self) -> int:
        return self.easy_solved + 3 * self.medium_solved + 5 * self.hard_solved

    class Config:
        from_attributes = True
