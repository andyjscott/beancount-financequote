"""Fetch prices using Perl's Finance::Quote exchange.
"""
__copyright__ = "Copyright (C) 2015-2016  Martin Blais"
__license__ = "GNU GPLv2"

from datetime import datetime
import os
import subprocess
import json
from dateutil import tz
import logging

from beancount.core.number import D
from beancount.prices import source
from beancount.utils import net_utils


class Source(source.Source):
    "Fetch prices using Perl's Finance::Quote module."

    def get_latest_price(self, ticker):
        """See contract in beancount.prices.source.Source."""

        path_to_script = os.path.abspath(os.path.dirname(__file__)) + "/financequote.pl"
        params = [path_to_script]

        if ":" in ticker:
            exchange, symbol = ticker.split(":", 1)
        else:
            # exchange and symbol were not both supplied
            return None

        params = [path_to_script, exchange, symbol]
        # output is a json object with keys in the form "$symbol\u001$variable"
        output = subprocess.check_output(params).decode()
        logging.debug("Finance::Quote: %s", output)
        info = json.loads(output)
        # remove the `symbol` prefix from the keys (+1 for control character)
        info = {x[len(symbol) + 1 :]: info[x] for x in info.keys()}

        if info.get("success") == 0:
            logging.error("Finance::Quote: %s", info.get("errormsg"))
            return None

        # `last` for stocks, `price` for currencies
        price = info.get("last", info.get("price"))
        if price is None:
            return None  # data was not able to be fetched

        currency = info["currency"]
        # Finance::Quote returns date in mm/dd/YY format
        trade_date = datetime.strptime(info["date"], "%m/%d/%Y").astimezone(
            tz=tz.tzlocal()
        )
        return source.SourcePrice(D(price), trade_date, currency)

    def get_historical_price(self, ticker, date):
        """See contract in beancount.prices.source.Source."""
        return None
