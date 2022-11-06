# Copyright (c) 2022 Graham Lea
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
# disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
# disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import logging
import operator
import sys
from datetime import date, timedelta
from logging import INFO
from pathlib import Path
from re import Pattern
from typing import List, Iterable, TypeVar, Optional, Callable, Any

T = TypeVar("T")

ARGUMENT_ERROR_STATUS = 2
CANT_CONTINUE_STATUS = 3
RUNTIME_ERROR_STATUS = 4
INVALID_FILE_FORMAT_STATUS = 5


def date_stream(from_date: date, to_date: date) -> Iterable[date]:
    """Yield a stream of dates"""
    i_date = from_date
    while i_date <= to_date:
        yield i_date
        i_date = i_date + timedelta(days=1)


def chunked(items: Iterable[T], chunk_size: int) -> Iterable[List[T]]:
    """Yield successive n-sized chunks from l."""
    items = list(items)
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


def twelve_months_ago() -> date:
    return (date.today() - timedelta(days=365)).replace(day=1)


def one_month_ago() -> date:
    the_date = date.today()
    if the_date.month != 1:
        return the_date.replace(month=the_date.month - 1)
    else:
        return the_date.replace(year=the_date.year - 1, month=12)


def yesterday() -> date:
    return date.today() - timedelta(days=1)


class YearMonth:
    year: int
    month: int

    def __init__(self, year: int, month: int):
        self.year = year
        self.month = month

    def first_date(self) -> date:
        return date(self.year, self.month, 1)

    def last_date(self) -> date:
        if self.month == 12:
            return date(self.year + 1, 1, 1) - timedelta(days=1)
        else:
            return date(self.year, self.month + 1, 1) - timedelta(days=1)

    def total_days(self) -> int:
        return (self.last_date() - self.first_date()).days + 1

    def minus_years(self, years: int) -> 'YearMonth':
        return YearMonth(self.year - years, self.month)

    def __eq__(self, o: object) -> bool:
        return isinstance(o, YearMonth) and o.year == self.year and o.month == self.month

    def __hash__(self) -> int:
        return operator.xor(self.year.__hash__(), self.month.__hash__())

    def __lt__(self, other):
        return self.year < other.year or (self.year == other.year and self.month < other.month)

    def __repr__(self):
        return f"{self.year}-{self.month:02d}"


def year_month(year_month_str: str) -> YearMonth:
    strings = year_month_str.split("-")
    if len(strings) != 2 or len(strings[0]) != 4 or len(strings[1]) != 2:
        raise ValueError(f"Invalid YearMonth string: '{year_month_str}'")
    year = int(strings[0])
    month = int(strings[1])
    if year < 2000 or year > 3000 or month < 1 or month > 12:
        raise ValueError(f"Invalid YearMonth string: '{year_month_str}'")
    return YearMonth(year, month)


def last_year_month() -> YearMonth:
    last_month = one_month_ago()
    return YearMonth(last_month.year, last_month.month)


FRIDAY_ISO_WEEKDAY = 5


class TariffCalendar:
    public_holiday_patterns: List[Pattern]

    def __init__(self, public_holiday_patterns: List[Pattern]) -> None:
        self.public_holiday_patterns = public_holiday_patterns

    def is_working_weekday(self, dt: date) -> bool:
        if dt.isoweekday() > FRIDAY_ISO_WEEKDAY:
            return False
        # It's a public holiday if this date matches any of the public holiday patterns
        date_string = dt.isoformat()
        if any((p.fullmatch(date_string) is not None for p in self.public_holiday_patterns)):
            return False
        return True


# Need to test TariffCalendar?
# with open("data/otherCharges/2021-2022/nsw.json5") as file_in:
#     tc = TariffCalendar(json5.load(file_in)["publicHolidayDatePatterns"])
#     print(f"tc.is_working_weekday(date(2021, 12, 28)): {tc.is_working_weekday(date(2021, 12, 28))}")
#     print(f"tc.is_working_weekday(date(2021, 12, 29)): {tc.is_working_weekday(date(2021, 12, 29))}")


def read_api_token_from_file(arg_parser) -> str:
    apitoken_file = Path(__file__).parent / "apitoken"
    if not apitoken_file.exists():
        arg_parser.print_usage(file=sys.stderr)
        exit(ARGUMENT_ERROR_STATUS)
    with open(apitoken_file) as apitoken_in:
        api_token = apitoken_in.read().strip()
    logging.info("API token loaded from ./apitoken")
    return api_token


def setup_stderr_logging():
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(logging.Formatter())
    logging.root.setLevel(INFO)
    # logging.root.setLevel(DEBUG)
    logging.root.addHandler(stderr_handler)


def check_python_version():
    # It might work with earlier versions, but I haven't tested
    if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 9):
        raise Exception("You must be using Python 3.9+ to run this tool.")


def read_and_convert_property(file_description: str, json_data: dict, property_name: str, allowed_types: set,
                              additional_msg: str, converter: Optional[Callable[[Any], Any]] = None):
    value = json_data.get(property_name)
    if value is None or not any((isinstance(value, t) for t in allowed_types)):
        logging.critical(
            f"ERROR: '{property_name}' must be in the {file_description} and {additional_msg}.")
        exit(INVALID_FILE_FORMAT_STATUS)

    if converter:
        try:
            value = converter(value)
        except:
            logging.critical(
                f"ERROR: '{property_name}' must be in the {file_description} and {additional_msg}.")
            exit(INVALID_FILE_FORMAT_STATUS)

    return value
