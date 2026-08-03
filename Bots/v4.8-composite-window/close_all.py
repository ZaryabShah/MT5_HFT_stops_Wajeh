"""Emergency kill switch: cancel all WajehGrid pendings and close all its
positions, then exit. Safe to run any time."""
import MetaTrader5 as mt5

import config as C
from bot import close_all, connect, log

if __name__ == "__main__":
    if connect():
        close_all()
        acc = mt5.account_info()
        log(f"Balance after flatten: {acc.balance:.2f} {acc.currency}")
        mt5.shutdown()
