slow="13.2 ms ± 828 μs per loop (mean ± std. dev. of 7 runs, 100 loops each)"
fast="87.5 μs ± 8.78 μs per loop (mean ± std. dev. of 7 runs, 10,000 loops each)"
def to_us(text):
    number,unit=text.split()[:2]
    return float(number)*{"s":1000000,"ms":1000,"μs":1,"µs":1,"ns":.001}[unit]
speedup=round(to_us(slow)/to_us(fast))
