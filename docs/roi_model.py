# ROI model for Google ads on the MERKANT Medien portal network.
# Edit ONE_OFF, MONTHLY and the scenarios, then run: python3 docs/roi_model.py
import math
ONE_OFF=3000; MONTHLY=100   # lean budget (original plan: ONE_OFF=12000, MONTHLY=900)
sc={'Conservative':(5e3,150e3,400e3,3.0),'Base':(10e3,400e3,1.2e6,5.0),'Optimistic':(20e3,1.0e6,3.0e6,8.0)}
def pv(m,a,b,c):
    if m<=12: return a*(b/a)**((m-1)/11)
    return b*(c/b)**((m-12)/12)
for name,(a,b,c,rpm) in sc.items():
    cum_rev=0;cum_cost=ONE_OFF;be=None;be_op=None;rows=[]
    for m in range(1,25):
        p=pv(m,a,b,c); r=p/1000*rpm
        cum_rev+=r; cum_cost+=MONTHLY
        if be_op is None and r>=MONTHLY: be_op=m
        if be is None and cum_rev>=cum_cost: be=m
        if m in (1,3,6,9,12,18,24): rows.append((m,p,r,r-MONTHLY,cum_rev-cum_cost))
        if m==12: roi12=(cum_rev-cum_cost)/cum_cost
    roi24=(cum_rev-cum_cost)/cum_cost
    print(f"\n## {name}: RPM {rpm} €")
    for m,p,r,pr,cp in rows: print(f"M{m:>2}: PV {p:>10,.0f} | rev {r:>8,.0f} € | profit/mo {pr:>8,.0f} € | cumulative {cp:>9,.0f} €")
    print(f"monthly break-even: M{be_op} | full payback: {('M'+str(be)) if be else '>24'} | ROI12 {roi12*100:.0f}% | ROI24 {roi24*100:.0f}% | 24m revenue {cum_rev:,.0f} € vs cost {cum_cost:,.0f} €")
# breakeven pageviews per RPM
print()
for rpm in (2,3,5,8,12): print(f"RPM {rpm}: PV/month to cover {MONTHLY} €: {MONTHLY/rpm*1000:,.0f}")
