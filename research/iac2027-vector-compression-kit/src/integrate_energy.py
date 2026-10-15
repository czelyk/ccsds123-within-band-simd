"""Integrate a real power log; no sample physical measurements are supplied.
CSV columns: time_s,power_w. Use CLOCK_MONOTONIC timestamps on the board,
or synchronize/trigger the instrument independently and quantify error.
"""
import argparse,csv,bisect,json
a=argparse.ArgumentParser();a.add_argument('csv');a.add_argument('--start',type=float,required=True);a.add_argument('--end',type=float,required=True);args=a.parse_args()
with open(args.csv) as f:rows=sorted((float(r['time_s']),float(r['power_w'])) for r in csv.DictReader(f))
if not args.start<args.end or len(rows)<2 or rows[0][0]>args.start or rows[-1][0]<args.end:raise SystemExit('Power log must bracket a nonempty interval.')
t=[r[0] for r in rows]
if any(t[i]>=t[i+1] for i in range(len(t)-1)):raise SystemExit('Times must be strictly increasing.')
def at(x):
    i=bisect.bisect_right(t,x)-1
    if i==len(rows)-1:return rows[i][1]
    return rows[i][1]+(rows[i+1][1]-rows[i][1])*(x-t[i])/(t[i+1]-t[i])
points=[(args.start,at(args.start))]+[r for r in rows if args.start<r[0]<args.end]+[(args.end,at(args.end))]
energy=sum((b[0]-a[0])*(a[1]+b[1])/2 for a,b in zip(points,points[1:]))
print(json.dumps({'energy_j':energy,'duration_s':args.end-args.start,'average_power_w':energy/(args.end-args.start),'maximum_log_gap_s':max(b[0]-a[0] for a,b in zip(points,points[1:]))}))
