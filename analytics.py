"""Transaction summaries used by the wallet dashboard."""

import datetime


def summarize_transactions(transactions, period_days=None, now=None):
    """Return money-in, money-out, fee, and count totals for a time period.

    ``period_days`` can be a positive number of days or ``None`` for all time.
    Recent-period summaries ignore transactions with invalid or out-of-range
    timestamps so malformed saved data cannot prevent the dashboard opening.
    """
    if period_days is not None and period_days <= 0:
        raise ValueError("The period must be a positive number of days.")

    now = now or datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=period_days) if period_days else None
    selected = []
    for transaction in transactions:
        if cutoff is not None:
            try:
                timestamp = datetime.datetime.strptime(
                    transaction.timestamp, "%Y-%m-%d %H:%M:%S",
                )
            except (TypeError, ValueError):
                continue
            if timestamp < cutoff or timestamp > now:
                continue
        selected.append(transaction)

    incoming_kinds = {"Deposit", "Transfer received"}
    outgoing_kinds = {"Withdrawal", "Transfer sent"}
    money_in = sum(
        transaction.amount for transaction in selected
        if transaction.kind in incoming_kinds
    )
    money_out = sum(
        transaction.amount for transaction in selected
        if transaction.kind in outgoing_kinds
    )
    fees = sum(transaction.fee for transaction in selected)

    return {
        "money_in": round(money_in, 2),
        "money_out": round(money_out, 2),
        "fees": round(fees, 2),
        "transaction_count": len(selected),
    }