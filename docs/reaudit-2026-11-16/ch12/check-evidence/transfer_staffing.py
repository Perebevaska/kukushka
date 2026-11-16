import math
rows=[(7,11),(6,7),(0,0),(18,7)]
for capacity in (4,6,8):
    counts=[(max(1,math.ceil(p/capacity)),max(1,math.ceil(y/capacity))) for p,y in rows]
    deficit=sum(max(n-p,0) for p,n in counts); extra=sum(max(p-n,0) for p,n in counts)
    for cost in (300,1200):
        print(capacity,cost,deficit,extra,cost*deficit+300*extra)
assert max(1,math.ceil(7/6))==max(1,math.ceil(11/6))==2
assert max(1,math.ceil(6/6))<max(1,math.ceil(7/6))
assert max(1,math.ceil(0/6))==1
