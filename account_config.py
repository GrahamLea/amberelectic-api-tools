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

from zoneinfo import ZoneInfo

from util import TariffCalendar


class AccountConfig:
    account_timezone: ZoneInfo
    calendar: TariffCalendar
    greenpower_active: bool
    feed_in_active: bool
    marginal_loss_factor: float
    amber_fee_dollars_inc_gst: float
    smart_meter_access_charge_cents_per_day: float

    def __init__(self,
                 account_timezone: ZoneInfo,
                 calendar: TariffCalendar,
                 greenpower_active: bool,
                 feed_in_active: bool,
                 marginal_loss_factor: float,
                 amber_fee_dollars_inc_gst: float,
                 smart_meter_access_charge_cents_per_day: float):
        self.account_timezone = account_timezone
        self.calendar = calendar
        self.greenpower_active = greenpower_active
        self.feed_in_active = feed_in_active
        self.marginal_loss_factor = marginal_loss_factor
        self.amber_fee_dollars_inc_gst = amber_fee_dollars_inc_gst
        self.smart_meter_access_charge_cents_per_day = smart_meter_access_charge_cents_per_day
