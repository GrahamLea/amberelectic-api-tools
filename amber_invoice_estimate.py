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
import re
import sys
import traceback
from typing import List, Dict
from zoneinfo import ZoneInfo

import amberelectric
import json5
from amberelectric.api import amber_api, AmberApi
from amberelectric.model.channel import ChannelType
from amberelectric.model.usage import Usage

from account_config import AccountConfig
from invoice import LineItem, Invoice
from sites import get_site
from tariff import Tariff
from usage import stream_usage_data
from util import setup_stderr_logging, read_api_token_from_file, check_python_version, RUNTIME_ERROR_STATUS, \
    year_month, last_year_month, INVALID_FILE_FORMAT_STATUS, YearMonth, TariffCalendar, read_and_convert_property


def main():
    arg_parser = \
        argparse.ArgumentParser(description="Estimates a monthly Amber Electric invoice for a given tariff")

    arg_parser.add_argument(
        "-t", "--api-token", required=False, default=None,
        help="Your Amber Electric API token. Alternatively, you can place your token in a file called 'apitoken'.")

    arg_parser.add_argument(
        "-s", "--site-id", required=False, default=None,
        help="The ID of the site for which to retrieve usage data. Only required if account has more than one site.")

    arg_parser.add_argument("account_config_file", type=argparse.FileType(),
                            help="A JSON5 file describing the account config to use in generating the estimate."
                                 " See files in the accountConfigs/ directory for examples.")

    arg_parser.add_argument("months", type=year_month, nargs="*", default=[last_year_month()],
                            help="A month, or months, to generate invoice estimates for, specified as YYYY-MM."
                                 " Defaults to the last month.")

    args = arg_parser.parse_args()

    setup_stderr_logging()

    api_token = args.api_token.strip() if args.api_token else read_api_token_from_file(arg_parser)

    amber_configuration = amberelectric.Configuration(access_token=api_token)
    client: AmberApi = amber_api.AmberApi.create(amber_configuration)

    site_id = args.site_id
    site = get_site(client, site_id)

    logging.info(f"Loading config...")

    feed_in_active = ChannelType.FEED_IN in {s.type for s in site.channels}
    logging.info(f"   Feed-in Active: {feed_in_active}")

    try:
        account_config_json = json5.load(args.account_config_file)
        assert isinstance(account_config_json, dict)
        logging.info(f"   Account config loaded from {args.account_config_file.name}")
    except Exception as ex:
        logging.critical("ERROR: The account config file could not be parsed: " + str(ex))
        exit(INVALID_FILE_FORMAT_STATUS)
        raise SystemExit

    account_timezone: ZoneInfo = read_and_convert_property(
        "Account Config", account_config_json, "timezone", {str},
        "must be a valid timezone name, e.g. Australia/Sydney", lambda s: ZoneInfo(s))

    logging.info(f"   Timezone: {account_timezone.key}")

    greenpower_active: bool = read_and_convert_property(
        "Account Config", account_config_json, "greenPowerActive", {bool}, "must be true or false")

    marginal_loss_factor: float = read_and_convert_property(
        "Account Config", account_config_json, "marginalLossFactor", {float}, "must be a decimal number")

    amber_fee_dollars_inc_gst: float = read_and_convert_property(
        "Account Config", account_config_json, "amberMonthlyFeeInDollarsIncGst", {float, int}, "must be a number")

    amber_fee_cents_ex_gst = round(amber_fee_dollars_inc_gst * 100 / 1.1)  # Remove GST

    tariff_files_by_channel_type = read_and_convert_property(
        "Account Config", account_config_json, "tariffsByChannelType", {dict},
        "must be an object mapping Channel Type names to tariffs")

    def read_other_charges(charges_description: str):
        oc_filename = "data/otherCharges/" + charges_description
        with open(oc_filename) as oc_file_in:
            json_content = json5.load(oc_file_in)
        logging.info(f"   Loaded {oc_filename}")
        return json_content

    other_charges_json = read_and_convert_property(
        "Account Config", account_config_json, "otherCharges", {str},
        "must be a string referencing file under data/otherCharges", converter=read_other_charges)

    public_holiday_patterns = read_and_convert_property(
        "Other Charges", other_charges_json, "publicHolidayDatePatterns", {list},
        "must be a list of date-matching regular expressions", converter=lambda ps: [re.compile(p) for p in ps])

    calendar = TariffCalendar(public_holiday_patterns)

    account_config = AccountConfig(account_timezone, calendar, greenpower_active, feed_in_active,
                                   marginal_loss_factor, amber_fee_dollars_inc_gst)
    other_charges = Tariff(other_charges_json, account_config)

    tariff_by_channel_type = dict()
    for ct, tariff_desc in tariff_files_by_channel_type.items():
        filename = "data/tariffs/" + tariff_desc
        with open(filename) as file_in:
            tariff_by_channel_type[ct] = Tariff(json5.load(file_in), account_config)
        logging.info(f"   Loaded tariff from {filename}")

    months = sorted(args.months)

    invoices: Dict[YearMonth, Invoice] = dict()

    for month in months:
        invoices[month] = calculate_invoice(client, site, month, tariff_by_channel_type, other_charges,
                                            amber_fee_dollars_inc_gst, amber_fee_cents_ex_gst)

    print_invoices(invoices)


def calculate_invoice(client, site, month, tariff_by_channel_type, other_charges, amber_fee_dollars_inc_gst,
                      amber_fee_cents_ex_gst):
    logging.info(f"Calculating invoice for {month}")
    usages: List[Usage] = list(stream_usage_data(client, site.id, month.first_date(), month.last_date()))
    general_usages: List[Usage] = list(filter(lambda u: u.channel_type == ChannelType.GENERAL, usages))
    controlled_usages: List[Usage] = list(filter(lambda u: u.channel_type == ChannelType.CONTROLLED_LOAD, usages))
    feed_in_usages: List[Usage] = list(filter(lambda u: u.channel_type == ChannelType.FEED_IN, usages))
    non_feed_in_usages: List[Usage] = general_usages + controlled_usages

    invoice = dict()
    usage_fees = invoice["Usage Fees"] = []
    general_tariff = tariff_by_channel_type[ChannelType.GENERAL.value]
    controlled_tariff = tariff_by_channel_type[ChannelType.CONTROLLED_LOAD.value]
    if general_usages:
        usage_fees.append(general_tariff.get_wholesales_fees_for(general_usages, "General Usage Wholesale"))
    if controlled_usages:
        usage_fees.append(controlled_tariff.get_wholesales_fees_for(controlled_usages, "Controlled Load Wholesale"))
    usage_fees += general_tariff.get_fee_lines_for(month, general_usages, lambda tc: tc.per_kwh_price_cents)
    usage_fees += controlled_tariff.get_fee_lines_for(month, controlled_usages, lambda tc: tc.per_kwh_price_cents)
    usage_fees += other_charges.get_fee_lines_for(month, non_feed_in_usages, lambda tc: tc.per_kwh_price_cents)
    # TODO: I don't actually know how/where Amber puts this on the bill
    if general_usages and any(c.per_peak_demand_kw_per_day_price_cents for c in general_tariff.components):
        invoice["Peak Demand Fees"] = \
            general_tariff.get_fee_lines_for(month, general_usages,
                                             lambda tc: tc.per_peak_demand_kw_per_day_price_cents)
    daily_fees = invoice["Daily Supply Fees"] = []
    # TODO: Metering charges not matching the bill. Why?
    #  https://github.com/amberelectric/public-api/discussions/50#discussioncomment-2235337
    daily_fees += general_tariff.get_fee_lines_for(month, general_usages, lambda tc: tc.per_day_price_cents)
    daily_fees += controlled_tariff.get_fee_lines_for(month, controlled_usages, lambda tc: tc.per_day_price_cents)
    days = month.total_days()
    invoice["Amber Fees"] = [
        LineItem(f"Amber - ${amber_fee_dollars_inc_gst} per month", days, amber_fee_cents_ex_gst / days,
                 amber_fee_cents_ex_gst)
    ]
    if feed_in_usages:
        # Include feed-in specific market charges in the one export line item
        solar_charges = \
            sum((sc.total_cost for sc in
                 other_charges.get_fee_lines_for(month, feed_in_usages, lambda tc: tc.per_kwh_price_cents)))

        invoice["Your Export Credits"] = [
            general_tariff.get_wholesales_fees_for(feed_in_usages, "Solar Exports", extra_charges=solar_charges,
                                                   invert_loss_factor=True, remove_gst=False, negate_total=True)
        ]
    return invoice


def print_invoices(invoices):
    for month, invoice in invoices.items():
        print("\n" + ("-" * 80))
        print(f"Month: {month}")
        total_cents = 0
        for section, items in invoice.items():
            print(f"\n   {section}:")
            for item in items:
                print(f"      {item.label:35s}   {item.amount_used:6.1f}   {item.unit_price:6.2f}"
                      f"   ${item.total_cost / 100:7.2f}")
                total_cents += item.total_cost

        solar_credits = -invoice["Your Export Credits"][0].total_cost if "Your Export Credits" in invoice else 0
        gst_cents = round((total_cents - solar_credits) * 0.1)  # No GST on exports
        total_cents = total_cents + gst_cents
        print(f"\n   TOTAL (incl. GST): ${total_cents / 100:7.2f}\n")


if __name__ == '__main__':
    check_python_version()
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        sys.stderr.flush()
        print(f"\nERROR: {e}", file=sys.stderr)
        exit(RUNTIME_ERROR_STATUS)
