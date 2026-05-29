def add_ema(data):

    data['EMA7'] = data['Close'].ewm(span=7).mean()
    data['EMA14'] = data['Close'].ewm(span=14).mean()
    data['EMA21'] = data['Close'].ewm(span=21).mean()

    return data


def add_all_indicators(data):
    """
    Add all technical indicators to the dataframe.
    Main wrapper function for indicator computation.
    """
    return add_ema(data)