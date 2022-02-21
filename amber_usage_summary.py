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
from datetime import date
from typing import Tuple, Dict, TypeVar

import amberelectric
from amberelectric.api import amber_api, AmberApi
from amberelectric.model.channel import ChannelType
from amberelectric.model.usage import Usage

from sites import get_site
from usage import stream_usage_data
from util import twelve_months_ago, yesterday, setup_stderr_logging, read_api_token_from_file, ARGUMENT_ERROR_STATUS, \
    check_python_version, RUNTIME_ERROR_STATUS

T = TypeVar("T")


class UsageSummary:
    """ A summary of usage data for a given date and Channel. """
    summary_date: date
    channel_id: str
    channel_type: ChannelType
    consumption_kwh: float
    cost_cents: float

    def __init__(self, initial_record: Usage) -> None:
        """ Initialises this object with the data from the given Usage record. """
        super().__init__()
        self.summary_date = initial_record.date
        self.channel_id = initial_record.channelIdentifier
        # noinspection PyTypeChecker
        self.channel_type = initial_record.channel_type
        self.consumption_kwh = 0.0
        self.cost_cents = 0.0

    def update(self, record: Usage):
        """ Adds the consumption and cost data from the given record to this summary. """
        self.consumption_kwh += record.kwh
        self.cost_cents += record.cost


def get_usage_summary(client: AmberApi, site_id: str, start_date: date, end_date: date) -> \
        Dict[Tuple[date, str], UsageSummary]:
    """
    Uses the given client to query the Amber API for all Usage data for the specified Site between the given dates
    (both inclusive), summarises the returned data by date and channel, and returns a dict of UsageSummary objects
    keyed by date and Channel ID.
    """
    summaries: Dict[Tuple[date, str], UsageSummary] = dict()  # Key is a tuple of date and Channel ID
    for record in stream_usage_data(client, site_id, start_date, end_date):
        summary = summaries.get((record.date, record.channelIdentifier))
        if not summary:
            summaries[(record.date, record.channelIdentifier)] = UsageSummary(record)
        else:
            summary.update(record)

    return summaries


def write_usage_summary_csv(usage_summaries_by_date_and_channel: Dict[Tuple[date, str], UsageSummary],
                            include_cost=False, file=sys.stdout):
    """
    Writes the data in the provided UsageSummary objects as a comma-separated value report to the specified file
    (stdout by default). If include_cost is true, an extra line will be printed for each Channel listing the cost.
    """
    all_dates_sorted = sorted(set(map(lambda dct: dct[0], usage_summaries_by_date_and_channel.keys())))

    # Print the header line
    channel_width = 32  # e.g. "E3 (CONTROLLED_LOAD) Usage (kWh)"
    channel_header_format = "{:" + str(channel_width) + "}"
    file.write(channel_header_format.format("CHANNEL"))
    for a_date in all_dates_sorted:
        file.write(f", {a_date.isoformat()}")
    file.write("\n")

    # Print the data lines
    all_channel_ids_sorted = sorted(set(map(lambda dct: dct[1], usage_summaries_by_date_and_channel.keys())))
    for channel_id in all_channel_ids_sorted:
        channel_type = next(
            filter(lambda us: us.channel_id == channel_id, usage_summaries_by_date_and_channel.values())
        ).channel_type

        # Write the consumption line
        file.write(channel_header_format.format(f"{channel_id} ({channel_type.name}) Usage (kWh)"))
        for a_date in all_dates_sorted:
            record = usage_summaries_by_date_and_channel.get((a_date, channel_id))
            # Length = 11 to match date width
            file.write(",{: 11.3f}".format(record.consumption_kwh if record else 0.0))
        file.write("\n")

        # Write the cost line
        if include_cost:
            file.write(channel_header_format.format(f"{channel_id} ({channel_type.name}) Cost ($)"))
            for a_date in all_dates_sorted:
                record = usage_summaries_by_date_and_channel.get((a_date, channel_id))
                # Length = 11 to match date width
                file.write(",{: 11.2f}".format((record.cost_cents / 100.0) if record else 0.0))
            file.write("\n")


def main():
    arg_parser = \
        argparse.ArgumentParser(description="Print daily summaries of Amber Electric usage data as a CSV report")

    arg_parser.add_argument(
        "-t", "--api-token", required=False, default=None,
        help="Your Amber Electric API token. Alternatively, you can place your token in a file called 'apitoken'.")

    arg_parser.add_argument(
        "-c", "--include-cost", required=False, action="store_true",
        help="Include a line in the report for the cost of usage in each Channel as well as the energy consumption. "
             "Defaults to false.")

    arg_parser.add_argument(
        "-s", "--site-id", required=False, default=None,
        help="The ID of the site for which to retrieve usage data. Only required if account has more than one site.")

    arg_parser.add_argument("start_date", type=date.fromisoformat, nargs="?", default=twelve_months_ago(),
                            help="The first date to include in the usage data report, as YYYY-MM-DD."
                                 " Defaults to 12 full calendar months ago.")

    arg_parser.add_argument("end_date", type=date.fromisoformat, nargs="?", default=yesterday(),
                            help="The last date to include in the usage data report, as YYYY-MM-DD. "
                                 "Defaults to yesterday.")

    args = arg_parser.parse_args()

    setup_stderr_logging()

    api_token = args.api_token.strip() if args.api_token else read_api_token_from_file(arg_parser)
    site_id = args.site_id
    include_cost = args.include_cost is True

    start_date = args.start_date
    end_date = args.end_date
    if end_date < start_date:
        logging.critical("ERROR: The end date cannot be before the start date.")
        exit(ARGUMENT_ERROR_STATUS)

    amber_configuration = amberelectric.Configuration(access_token=api_token)
    client: AmberApi = amber_api.AmberApi.create(amber_configuration)

    site = get_site(client, site_id)
    write_usage_summary_csv(get_usage_summary(client, site.id, start_date, end_date), include_cost=include_cost)


if __name__ == '__main__':
    check_python_version()
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        sys.stderr.flush()
        print(f"\nERROR: {e}", file=sys.stderr)
        exit(RUNTIME_ERROR_STATUS)
