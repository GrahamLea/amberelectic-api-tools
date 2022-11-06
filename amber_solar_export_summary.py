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
from typing import Dict, TypeVar

import amberelectric
from amberelectric.api import amber_api, AmberApi
from amberelectric.model.channel import ChannelType
from amberelectric.model.usage import Usage

from sites import get_site
from usage import stream_usage_data
from util import setup_stderr_logging, read_api_token_from_file, ARGUMENT_ERROR_STATUS, \
    check_python_version, RUNTIME_ERROR_STATUS, YearMonth, year_month, last_year_month

T = TypeVar("T")


class SolarExportDailySummary:
    """ A summary of solar export data for a given day. """
    summary_date: date
    peak_period_kw: float
    total_kwh: float
    total_income_cents: float

    def __init__(self, summary_date: date) -> None:
        """ Initialises this object with the data from the given Usage record. """
        super().__init__()
        self.summary_date = summary_date
        self.peak_period_kw = 0.0
        self.total_kwh = 0.0
        self.total_income_cents = 0.0

    def update(self, record: Usage):
        """ Adds the consumption and cost data from the given record to this summary. """
        kw_in_record = record.kwh * (60 / int(record.duration))  # kWh -> kW, e.g. 30 min. kWh x 2 = kW
        self.peak_period_kw = max(self.peak_period_kw, kw_in_record)
        self.total_kwh += record.kwh
        self.total_income_cents += (-record.cost)


class SolarExportMonthlySummary:
    """ A summary of solar export data for a given month. """
    year_month: YearMonth

    total_kwh: float
    total_income_cents: float
    average_daily_kwh: float
    peak_daily_kwh: float
    peak_period_kw: float

    days_covered: int

    def __init__(self, summary_year_month: YearMonth) -> None:
        """ Initialises this object with the data from the given Usage record. """
        super().__init__()
        self.year_month = summary_year_month

        self.total_kwh = 0
        self.total_income_cents = 0.0
        self.average_daily_kwh = 0.0
        self.peak_daily_kwh = 0.0
        self.peak_period_kw = 0

        self.days_covered = 0

    def update(self, daily_summary: SolarExportDailySummary):
        """ Adds the data from the given daily summary to this monthly summary. """
        self.total_kwh += daily_summary.total_kwh
        self.total_income_cents += daily_summary.total_income_cents

        day_kwh = daily_summary.total_kwh
        self.peak_daily_kwh = max(self.peak_daily_kwh, day_kwh)

        new_average = ((self.average_daily_kwh * self.days_covered) + day_kwh) / (self.days_covered + 1)
        self.average_daily_kwh = new_average
        self.days_covered += 1

        self.peak_period_kw = max(self.peak_period_kw, daily_summary.peak_period_kw)


def get_solar_export_daily_summaries(client: AmberApi, site_id: str, start_date: date, end_date: date) -> \
        Dict[date, SolarExportDailySummary]:
    """
    Uses the given client to query the Amber API for all Usage data for the specified Site between the given dates
    (both inclusive), summarises the returned data by date, and returns a dict of SolarExportDailySummary objects
    keyed by date.
    """
    summaries: Dict[date, SolarExportDailySummary] = dict()
    for record in stream_usage_data(client, site_id, start_date, end_date):
        if record.channel_type == ChannelType.FEED_IN:
            summary = summaries.get(record.date)
            if not summary:
                summaries[record.date] = summary = SolarExportDailySummary(record.date)
            summary.update(record)

    return summaries


def get_solar_export_monthly_summary(client: AmberApi, site_id: str, start_month: YearMonth, end_month: YearMonth) -> \
        Dict[YearMonth, SolarExportMonthlySummary]:
    """
    Uses the given client to query the Amber API for all Usage data for the specified Site between the given dates
    (both inclusive), summarises the returned data by month, and returns a dict of SolarExportSummary objects
    keyed by month.
    """
    summaries: Dict[YearMonth, SolarExportMonthlySummary] = dict()
    for daily_summary in \
            get_solar_export_daily_summaries(client, site_id, start_month.first_date(), end_month.last_date()).values():
        summary_year_month = YearMonth(daily_summary.summary_date.year, daily_summary.summary_date.month)
        summary = summaries.get(summary_year_month)
        if not summary:
            summaries[summary_year_month] = SolarExportMonthlySummary(summary_year_month)
        else:
            summary.update(daily_summary)

    return summaries


def write_solar_export_summary_csv(summaries_by_year_month: Dict[YearMonth, SolarExportMonthlySummary],
                                   file=sys.stdout):
    """
    Writes the data in the provided SolarExportMonthlySummary objects as a comma-separated value report to the
    specified file (stdout by default).
    """
    all_months_sorted = sorted(summaries_by_year_month.keys())

    metrics = {
        "Total kWh": lambda s: s.total_kwh,
        "Total Income $": lambda s: round(s.total_income_cents / 100, 2),
        "Average Daily kWh": lambda s: s.average_daily_kwh,
        "Peak Daily kWh": lambda s: s.peak_daily_kwh,
        "Peak Period kW": lambda s: s.peak_period_kw
    }

    max_label_width = max(map(len, metrics.keys()))

    # Print the header line
    metric_header_format = "{:" + str(max_label_width) + "}"
    file.write(metric_header_format.format(""))
    for a_month in all_months_sorted:
        file.write(f", {a_month}")
    file.write("\n")

    # Print the data lines
    for metric_label, metric_fn in metrics.items():
        file.write(metric_header_format.format(metric_label))
        for a_month in all_months_sorted:
            record = summaries_by_year_month.get(a_month)
            # Length = 8 to match " YYYY-DD" width
            file.write(",{: 8.3f}".format(metric_fn(record)))
        file.write("\n")


def main():
    arg_parser = argparse.ArgumentParser(
        description="Print monthly summaries of Amber Electric solar export data as a CSV report")

    arg_parser.add_argument(
        "-t", "--api-token", required=False, default=None,
        help="Your Amber Electric API token. Alternatively, you can place your token in a file called 'apitoken'.")

    arg_parser.add_argument(
        "-s", "--site-id", required=False, default=None,
        help="The ID of the site for which to retrieve usage data. Only required if account has more than one site.")

    arg_parser.add_argument("start_month", type=year_month, nargs="?", default=last_year_month().minus_years(1),
                            help="The first month to include in the usage data report, as YYYY-MM."
                                 " Defaults to 12 full calendar months ago.")

    arg_parser.add_argument("end_month", type=year_month, nargs="?", default=last_year_month(),
                            help="The last month to include in the usage data report, as YYYY-MM. "
                                 "Defaults to the last month.")

    args = arg_parser.parse_args()

    setup_stderr_logging()

    api_token = args.api_token.strip() if args.api_token else read_api_token_from_file(arg_parser)
    site_id = args.site_id

    start_month: YearMonth = args.start_month
    end_month: YearMonth = args.end_month
    if end_month < start_month:
        logging.critical("ERROR: The end date cannot be before the start date.")
        exit(ARGUMENT_ERROR_STATUS)

    amber_configuration = amberelectric.Configuration(access_token=api_token)
    client: AmberApi = amber_api.AmberApi.create(amber_configuration)

    site = get_site(client, site_id)
    write_solar_export_summary_csv(get_solar_export_monthly_summary(client, site.id, start_month, end_month))


if __name__ == '__main__':
    check_python_version()
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        sys.stderr.flush()
        print(f"\nERROR: {e}", file=sys.stderr)
        exit(RUNTIME_ERROR_STATUS)
