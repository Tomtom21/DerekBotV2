def get_suffix(n):
    """
    Gets the numeric suffix for any integer

    :param n: An integer
    :return: The numeric suffix
    """
    if n < 0:
        raise Exception("Negative numbers are not allowed")

    if n % 100 in [11, 12, 13]:
        return 'th'
    if n % 10 == 1:
        return 'st'
    if n % 10 == 2:
        return 'nd'
    if n % 10 == 3:
        return 'rd'
    return 'th'
