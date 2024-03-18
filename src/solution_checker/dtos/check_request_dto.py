from typing import Annotated, Any

from annotated_types import Len

from src.common.dtos.base_dto import BaseDTO


class CheckRequestDTO(BaseDTO, frozen=True):
    source_code: dict[str, Any]
    tests: list[Annotated[list[str], Len(max_length=2)]]
    build_timeout: int | None = None
    test_timeout: int | None = None
