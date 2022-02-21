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
import sys
from datetime import date, timedelta
from logging import INFO
from pathlib import Path
from typing import List, Iterable, TypeVar

T = TypeVar("T")

ARGUMENT_ERROR_STATUS = 2
CANT_CONTINUE_STATUS = 2
RUNTIME_ERROR_STATUS = 4


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
    logging.root.addHandler(stderr_handler)


def check_python_version():
    # It might work with earlier versions, but I haven't tested
    if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 9):
        raise Exception("You must be using Python 3.9+ to run this tool.")
