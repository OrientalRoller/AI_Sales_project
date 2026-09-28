from pydantic import BaseModel
from typing import List, Optional

# 1. Define the Schema 
class ProspectProfile(BaseModel):
    first_name: Optional[str] = "Unknown"
    last_name: Optional[str] = ""
    current_role: Optional[str] = "Unknown Role"
    company_name: Optional[str] = "Unknown Company"
    recent_achievements: Optional[List[str]] = []
    inferred_interests: Optional[List[str]] = []