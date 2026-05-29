def generate_signal(data):

    latest = data.iloc[-1]

    if latest['EMA7'] > latest['EMA14'] > latest['EMA21']:
        return "BUY"

    elif latest['EMA7'] < latest['EMA14'] < latest['EMA21']:
        return "SELL"

    else:
        return "HOLD"


def generate_signals(data):
    """
    Add a signal column to the dataframe.
    Each row gets the signal derived from data up to that point.
    """
    if data is None or data.empty:
        return data

    result = data.copy()
    result["signal"] = "HOLD"

    for index in range(len(result)):
        if index < 2:
            continue
        subset = result.iloc[: index + 1]
        result.iloc[index, result.columns.get_loc("signal")] = generate_signal(subset)

    return result


def latest_signal(data):
    """
    Get the latest signal from the data.
    Alias for generate_signal.
    """
    if data is None or data.empty:
        return "HOLD"
    if "signal" in data.columns:
        value = data.iloc[-1]["signal"]
        return value if isinstance(value, str) else "HOLD"
    return generate_signal(data)