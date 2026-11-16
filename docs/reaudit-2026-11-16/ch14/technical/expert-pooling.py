"""Sobel x with nearest padding on identical rows, exactly as in 02-filters/global."""
from statistics import mean
def abs_response(row):
    # SX has column sums -4, 0, 4. A vertical copy of a row makes y padding irrelevant.
    last = len(row) - 1
    return [abs(4 * (row[min(i+1,last)] - row[max(i-1,0)])) for i in range(len(row))]

for row in ([1,1,0,0], [0,1,1,0]):
    response = abs_response(row)
    print(row, response, mean(response))
