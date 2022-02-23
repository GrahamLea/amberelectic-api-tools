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
from operator import attrgetter
from typing import Optional

import amberelectric
from amberelectric.api import AmberApi
from amberelectric.model.site import Site

from util import ARGUMENT_ERROR_STATUS, CANT_CONTINUE_STATUS


def get_site(client: AmberApi, site_id: Optional[str]) -> Site:
    """
    Queries the given client for Sites and returns:
     -  if site_id is specified and a Site with that ID is found, that Site; or
     -  if site_id is not specified and a single Site is found, that single Site
    Exits after logging if any other states occur.
    """
    try:
        logging.info("Retrieving sites")
        sites = client.get_sites()
        logging.info("    Done")
    except amberelectric.ApiException as ex:
        if ex.status == 403:
            logging.critical("ERROR: The request was forbidden. That probably means your API token is invalid.")
            exit(ARGUMENT_ERROR_STATUS)
        raise RuntimeError(f"We failed to retrieve a list of Amber sites because of an error: {ex}") from ex
    if len(sites) == 0:
        logging.critical("ERROR: No sites were found in the Amber account.")
        exit(CANT_CONTINUE_STATUS)

    if not site_id:
        if len(sites) == 1:
            return sites[0]
        else:
            logging.critical(f"ERROR: There are multiple sites in this Amber account.")
            logging.critical(f"       Use the --site-id (or -s) argument to specify which one should be queried.")
            logging.critical(f"       Available Site IDs are: {list(map(attrgetter('id'), sites))}")
            exit(CANT_CONTINUE_STATUS)
    else:
        matching_sites = list(filter(lambda s: s.id == site_id, sites))
        if len(matching_sites) == 0:
            logging.critical(f"ERROR: The Site ID specified as an argument ('{site_id}') was not found in the account.")
            logging.critical(f"       Available Site IDs are: {list(map(attrgetter('id'), sites))}")
            exit(ARGUMENT_ERROR_STATUS)
        elif len(matching_sites) > 1:
            logging.critical(f"WEIRDNESS! The API returned more than one Site with the specified Site ID. 😬")
            exit(CANT_CONTINUE_STATUS)
        else:
            return matching_sites[0]

    raise RuntimeError("This line should never be reached unless exit() doesn't exit. 🤷🏻‍")
