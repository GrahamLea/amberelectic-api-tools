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
from typing import Optional, List, Callable, TypeVar, Any

from amberelectric.model.channel import ChannelType
from amberelectric.model.tariff_information import PeriodType
from amberelectric.model.usage import Usage

from account_config import AccountConfig
from invoice import LineItem
from util import YearMonth

T = TypeVar("T")


def check_bool(val: Any) -> bool:
    if val is True or val is False:
        return val
    raise ValueError("Not a bool")


class TariffComponent:
    account_config: AccountConfig
    dnsp_label: Optional[str]
    amber_label: str
    usage_filters: List[Callable[[Usage], bool]]
    greenpower_filter: Optional[Callable[[bool], bool]]
    feed_in_filter: Optional[Callable[[bool], bool]]
    month_filter: Optional[Callable[[int], bool]]
    per_kwh_price_cents: float
    per_day_price_cents: float
    per_peak_demand_kw_per_day_price_cents: float

    def __init__(self, tariff_component_json: dict, account_config: AccountConfig):
        self.account_config = account_config
        if "amberLabel" not in tariff_component_json:
            raise ValueError(
                "Required property 'amberLabel' not found in tariff component: " + str(tariff_component_json))
        self.amber_label = tariff_component_json["amberLabel"]
        self.dnsp_label = tariff_component_json.get("dnspLabel")
        self.usage_filters = [
            create_usage_filter(tariff_component_json, "periodFilter", PeriodType.from_str,
                                lambda usage: usage.tariff_information.period),
            create_usage_filter(tariff_component_json, "channelTypeFilter", ChannelType.from_str,
                                lambda usage: usage.channel_type),
            create_usage_filter(tariff_component_json, "hourFilter", lambda x: int(x),
                                lambda usage: usage.start_time.astimezone(account_config.account_timezone).hour),
            create_usage_filter(tariff_component_json, "workingWeekdayFilter", check_bool,
                                lambda usage: account_config.calendar.is_working_weekday(usage.date))
        ]
        self.usage_filters = list(filter(None, self.usage_filters))

        if "greenPowerFilter" in tariff_component_json:
            greenpower_pass_val = tariff_component_json["greenPowerFilter"]
            self.greenpower_filter = lambda greenpower_active: greenpower_active == greenpower_pass_val
        else:
            self.greenpower_filter = None

        if "feedInFilter" in tariff_component_json:
            feed_in_pass_val = tariff_component_json["feedInFilter"]
            self.feed_in_filter = lambda feed_in_active: feed_in_active == feed_in_pass_val
        else:
            self.feed_in_filter = None

        if "monthFilter" in tariff_component_json:
            month_values = tariff_component_json["monthFilter"]
            if not (isinstance(month_values, list) and all([isinstance(v, int) for v in month_values])):
                raise ValueError("'monthFilter' in a tariff component must be a list of months as integers")
            self.month_filter = lambda month: month in month_values
        else:
            self.month_filter = None

        self.per_kwh_price_cents = tariff_component_json.get("centsPerKwh")
        self.per_day_price_cents = tariff_component_json.get("centsPerDay")
        self.per_peak_demand_kw_per_day_price_cents = tariff_component_json.get("centsPerPeakDemandKwPerDay")

        if len(list(filter(None, [self.per_kwh_price_cents, self.per_day_price_cents,
                                  self.per_peak_demand_kw_per_day_price_cents]))) != 1:
            raise ValueError(
                "Tariff components should have exactly one of centsPerKwh, centsPerDay, or centsPerPeakDemandKwPerDay")

    def create_line_for_component(self, month: YearMonth, base_usages: List[Usage]) -> Optional[LineItem]:
        component_name = self.dnsp_label or self.amber_label
        if self.greenpower_filter and not self.greenpower_filter(self.account_config.greenpower_active):
            logging.debug(
                f"   Ignoring component '{component_name}' due to non-matching greenpower active"
                f" ({self.account_config.greenpower_active})")
            return None
        if self.feed_in_filter and not self.feed_in_filter(self.account_config.feed_in_active):
            logging.debug(
                f"   Ignoring component '{component_name}' due to non-matching feed-in active"
                f" ({self.account_config.feed_in_active})")
            return None
        if self.month_filter and not self.month_filter(month.month):
            logging.debug(f"   Ignoring component '{component_name}' due to non-matching month ({month.month})")
            return None

        if self.per_day_price_cents:
            amount = month.total_days()
            unit_price = self.per_day_price_cents
        else:
            logging.debug(f"   Filtering for {self.dnsp_label or self.amber_label}")
            filtered_usages = filter_usages(base_usages, self)
            if self.per_kwh_price_cents:
                amount = sum([u.kwh for u in filtered_usages])
                unit_price = self.per_kwh_price_cents
            elif self.per_peak_demand_kw_per_day_price_cents:
                # NOTE: This will break if 5 min windows becomes the default?
                peak_demand_usage = max(filtered_usages, key=lambda u: u.kwh)
                peak_demand_kw = peak_demand_usage.kwh * 2
                logging.info(f"   Peak demand for {month} found at "
                             f"{peak_demand_usage.start_time.astimezone(self.account_config.account_timezone)}"
                             f" = {peak_demand_usage.kwh} kWh in 30 min = {peak_demand_kw} kW")
                amount = month.total_days()
                unit_price = self.per_peak_demand_kw_per_day_price_cents * peak_demand_kw
            else:
                raise RuntimeError("TariffComponent doesn't have any known price property")

        total_cost_cents = round(amount * unit_price)
        return LineItem(self.amber_label, amount, unit_price, total_cost_cents) if total_cost_cents != 0 else None


class Tariff:
    account_config: AccountConfig
    distribution_loss_factor: float
    components: List[TariffComponent]

    def __init__(self, tariff_json: dict, account_config: AccountConfig):
        self.account_config = account_config
        if not isinstance(tariff_json, dict):
            raise ValueError("Tariff JSON must be an object")
        components = tariff_json.get("components")
        if not isinstance(components, list):
            raise ValueError(
                "Tariff JSON must contain a property 'components', a list of objects (one for each tariff component)")

        self.distribution_loss_factor = tariff_json.get("distributionLossFactor", 1.0)
        self.components = [TariffComponent(cj, account_config) for cj in components]

    def get_wholesales_fees_for(self, usages: List[Usage], label: str, extra_charges=0, invert_loss_factor=False,
                                remove_gst=True, negate_total=False) -> LineItem:
        # NOTE: For Feed-In, amounts are all calculated as positives, then negated in final line item.
        loss_factor = self.distribution_loss_factor * self.account_config.marginal_loss_factor
        if invert_loss_factor:
            loss_factor = 1 / loss_factor
        total_fees = sum([u.kwh * u.spot_per_kwh for u in usages]) * loss_factor
        if remove_gst:
            total_fees = total_fees / 1.1
        total_fees += extra_charges
        total_amount_cents = round(total_fees)

        total_kwh = sum([u.kwh for u in usages])
        per_kwh_average_cost = total_amount_cents / total_kwh if total_kwh else 0

        if negate_total:
            total_amount_cents = -total_amount_cents
        return LineItem(label, total_kwh, per_kwh_average_cost, total_amount_cents)

    def get_fee_lines_for(self, month: YearMonth, base_usages: List[Usage],
                          tariff_component_filter: Callable[[TariffComponent], bool]) -> List[LineItem]:
        result = []
        if base_usages:
            for component in (c for c in self.components if tariff_component_filter(c)):
                if line_item := component.create_line_for_component(month, base_usages):
                    result.append(line_item)
        return result


def filter_usages(base_usages, component):
    filtered_usages: List[Usage] = base_usages
    for usage_filter in component.usage_filters:
        count_before = len(filtered_usages)
        filtered_usages = list(filter(usage_filter, filtered_usages))
        logging.debug(f"      {usage_filter.filter_name}: {count_before} -> {len(filtered_usages)}")
    return filtered_usages


def create_usage_filter(component_json: dict, filter_property_name: str,
                        filter_type_constructor_and_validator: Callable[[Any], T],
                        usage_attribute_selector: Callable[[Usage], T]) \
        -> Optional[Callable[[Usage], bool]]:
    if filter_property_name in component_json:
        json_filter_values = component_json[filter_property_name]
        if isinstance(json_filter_values, bool):
            json_filter_values = [json_filter_values]
        if not isinstance(json_filter_values, list):
            raise ValueError(f"'{filter_property_name}' in a tariff component must be a list of values")
        typed_filter_values = {filter_type_constructor_and_validator(f) for f in json_filter_values}

        def usage_filter(usage: Usage) -> bool:
            return usage_attribute_selector(usage) in typed_filter_values

        usage_filter.filter_name = f"{filter_property_name}({json_filter_values})"
        return usage_filter
    else:
        return None
