# Calculates the suffix for a provided numeric value
def get_suffix(n):
    if n < 0: raise Exception("Ordinal negative numbers are not allowed")
    if n % 100 in [11, 12, 13]: return 'th'
    if n % 10 == 1: return 'st'
    if n % 10 == 2: return 'nd'
    if n % 10 == 3: return 'rd'
    return 'th'
