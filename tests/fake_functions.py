import datetime as dt
from decimal import Decimal
from typing import Any, cast

from faker import Faker

fake = Faker(['pt_BR'])


def country_code() -> str:
    return cast(str, fake.unique.country_code())


def fake_decimal(
    left_digits: int | None = None,
    right_digits: int = 2,
    min_value: int = 0,
    max_value: int = 10000,
) -> Decimal:
    return cast(
        Decimal,
        fake.pydecimal(
            left_digits=left_digits,
            right_digits=right_digits,
            min_value=min_value,
            max_value=max_value,
        ),
    )


def fake_cpf(*, with_separators: bool = False) -> str:
    if with_separators:
        return cast(str, fake.cpf())
    return cast(str, fake.ssn())


def fake_email() -> str:
    return cast(str, fake.email())


def fake_date_time() -> dt.datetime:
    return cast(dt.datetime, fake.date_time(tzinfo=dt.timezone.utc))


def fake_dict() -> dict[str, Any]:
    return cast(dict[str, Any], fake.pydict())


def fake_url() -> str:
    return cast(str, fake.uri())
