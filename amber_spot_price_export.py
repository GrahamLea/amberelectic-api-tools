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

import argparse
import logging
import sys
import traceback
from collections import defaultdict
from datetime import date
from operator import attrgetter
from typing import Tuple, Dict, TypeVar, List

import amberelectric
from amberelectric.api import amber_api, AmberApi
from amberelectric.model.actual_interval import ActualInterval
from amberelectric.model.channel import ChannelType

from prices import stream_price_data
from sites import get_site
from util import one_month_ago, yesterday, check_python_version, setup_stderr_logging, read_api_token_from_file

T = TypeVar("T")

ARGUMENT_ERROR_STATUS = 2
CANT_CONTINUE_STATUS = 2
RUNTIME_ERROR_STATUS = 4


def get_prices(client: AmberApi, site_id: str, start_date: date, end_date: date) -> \
        Dict[Tuple[date, ChannelType], List[ActualInterval]]:
    """
    Uses the given client to query the Amber API for all Usage data for the specified Site between the given dates
    (both inclusive), summarises the returned data by date and channel, and returns a dict of UsageSummary objects
    keyed by date and Channel ID.
    """
    summaries: Dict[Tuple[date, ChannelType], List[ActualInterval]] = defaultdict(
        list)  # Key is a tuple of date and Channel ID
    for interval in stream_price_data(client, site_id, start_date, end_date):
        summaries[(interval.date, interval.channel_type)].append(interval)

    for k, intervals in summaries.items():
        intervals.sort(key=attrgetter("start_time"))
    return summaries


def write_prices_csv(prices: Dict[Tuple[date, ChannelType], List[ActualInterval]], file=sys.stdout):
    """
    Writes the data in the provided prices objects as a comma-separated value report to the specified file
    (stdout by default).
    """
    all_dates_sorted = sorted({k[0] for k in prices})
    all_times_sorted = sorted({ai.nem_time.time() for v in prices.values() for ai in v})

    # Print the header line
    file.write("{:11}".format("DATE +10:00"))
    channel_type_width = 23  # "CONTROLLED_LOAD (c/kWh)"
    channel_header_format = ", {:" + str(channel_type_width) + "}"
    file.write(channel_header_format.format("CHANNEL"))
    for a_time in all_times_sorted:
        file.write(f", {a_time.isoformat()}")
    file.write("\n")

    # Print the data lines
    for a_date in all_dates_sorted:
        for channel_type in [ChannelType.GENERAL, ChannelType.CONTROLLED_LOAD, ChannelType.FEED_IN]:
            if intervals := prices.get((a_date, channel_type)):
                file.write(a_date.isoformat() + " ")
                file.write(channel_header_format.format(channel_type.name + " (c/kWh)"))

                intervals_by_time: Dict[str, ActualInterval] = {i.nem_time.time(): i for i in intervals}
                for a_time in all_times_sorted:
                    if interval := intervals_by_time.get(a_time):
                        # Length = 9 to match time width " 12:30:00"
                        file.write(",{: 9.3f}".format(interval.per_kwh))
                    else:
                        file.write(",{:9}".format("X"))
                file.write("\n")


def main():
    arg_parser = \
        argparse.ArgumentParser(description="Print spot prices from Amber Electric as a CSV report")

    arg_parser.add_argument(
        "-t", "--api-token", required=False, default=None,
        help="Your Amber Electric API token. Alternatively, you can place your token in a file called 'apitoken'.")

    arg_parser.add_argument(
        "-s", "--site-id", required=False, default=None,
        help="The ID of the site for which to retrieve usage data. Only required if account has more than one site.")

    arg_parser.add_argument("start_date", type=date.fromisoformat, nargs="?", default=one_month_ago(),
                            help="The first date to include in the usage data report, as YYYY-MM-DD."
                                 " Defaults to 1 calendar month ago.")

    arg_parser.add_argument("end_date", type=date.fromisoformat, nargs="?", default=yesterday(),
                            help="The last date to include in the usage data report, as YYYY-MM-DD. "
                                 "Defaults to yesterday.")

    args = arg_parser.parse_args()

    setup_stderr_logging()

    api_token = args.api_token.strip() if args.api_token else read_api_token_from_file(arg_parser)
    site_id = args.site_id

    start_date = args.start_date
    end_date = args.end_date
    logging.info(f"Start date: {start_date}")
    logging.info(f"End date: {end_date}")
    if end_date < start_date:
        logging.critical("ERROR: The end date cannot be before the start date.")
        exit(ARGUMENT_ERROR_STATUS)

    amber_configuration = amberelectric.Configuration(access_token=api_token)
    client: AmberApi = amber_api.AmberApi.create(amber_configuration)

    site = get_site(client, site_id)
    write_prices_csv(get_prices(client, site.id, start_date, end_date))


if __name__ == '__main__':
    check_python_version()
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        sys.stderr.flush()
        print(f"\nERROR: {e}", file=sys.stderr)
        exit(RUNTIME_ERROR_STATUS)
