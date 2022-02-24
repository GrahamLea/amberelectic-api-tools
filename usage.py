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
from datetime import date
from typing import List, Iterable

import amberelectric
from amberelectric.api import AmberApi
from amberelectric.model.usage import Usage

from util import chunked, date_stream


def stream_usage_data(client: AmberApi, site_id: str, start_date: date, end_date: date) -> Iterable[Usage]:
    """
    Uses the given client to query the Amber API for all Usage data for the specified Site between the given dates
    (both inclusive), and returns a generator that streams Usage objects.
    """
    # Do requests in batches. API couldn't handle large responses in testing. (2021-09-11)
    for date_range in chunked(date_stream(start_date, end_date), 10):
        batch_start = date_range[0]
        batch_end = date_range[-1]
        try:
            logging.info(f"   Retrieving usage: {batch_start} -> {batch_end}")
            # noinspection PyTypeChecker
            usage_records: List[Usage] = client.get_usage(site_id, batch_start, batch_end)
            logging.info("       Done")
            for ur in usage_records:
                yield ur
        except amberelectric.ApiException as ex:
            raise RuntimeError(f"We failed to retrieve your Amber usage stats because of an error: {ex}") from ex
