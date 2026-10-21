from typing import Annotated, List
from pydantic import Field, StringConstraints

# Tool arguments are chosen by the LLM, so they are checked like user input.
Place = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80, pattern=r"^[\w ,.'()-]+$")]
CurrencyCode = Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^[A-Za-z]{3}$")]
Money = Annotated[float, Field(ge=0, le=1_000_000_000)]
Days = Annotated[int, Field(ge=1, le=60)]
Costs = Annotated[List[Money], Field(min_length=1, max_length=100)]
