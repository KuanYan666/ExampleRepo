"""The supermarket is a nested system: outdoors -> store -> freezer case.
How much does the STORE's front door change the FREEZER's energy bill?"""
import core as C
CP, H_SUB = 1.006, 2835.0
CASE = (-18.0, 90.0)
W_case = C.W_from_RH(*CASE)

def case_load_per_kg(T_store, RH_store):
    W = C.W_from_RH(T_store, RH_store)
    sens = CP * (T_store - CASE[0])
    lat = (W - W_case) * H_SUB
    return sens, lat, W

print("="*74); print("HOW STORE AIR CHANGES THE FREEZER'S LOAD"); print("="*74)
print(f"{'store air':>22} | {'W':>7} | {'sensible':>9} {'latent':>8} {'total':>8} | vs base")
base = None
for T,RH,tag in [(24,45,"dry winter store"),(24,55,"baseline"),(24,65,"doors busy, summer"),
                 (24,75,"humid day, doors open"),(26,65,"hot day, doors open")]:
    s,l,W = case_load_per_kg(T,RH)
    tot = s+l
    if base is None: base = tot
    print(f"{tag:>22} | {W*1000:5.2f}gk | {s:8.1f} {l:8.1f} {tot:8.1f} | {100*(tot/base-1):+5.1f}%")

print()
print("  -> the freezer never touches the outside air, yet the shop's front door")
print("     moves its energy bill by double digits. THIS IS THE NESTED EFFECT.")

print(); print("="*74); print("NET HEAT THE WHOLE FREEZER ADDS TO THE SHOP"); print("="*74)
Q_load, COP = 2.5, 1.7
W_el = Q_load/COP; Q_rej = Q_load + W_el
print(f"  case pulls out of the aisle air      : -{Q_load:.2f} kW  (it chills the aisle)")
print(f"  condenser dumps back into the shop   : +{Q_rej:.2f} kW")
print(f"  NET into the shop                    : {Q_rej-Q_load:+.2f} kW")
print(f"  ...which equals the electricity used : {W_el:.2f} kW   <- exactly. Nothing else can happen.")
print()
print("  BUT it is not spread evenly:")
print(f"    the frozen aisle gets COLDER by {Q_load:.2f} kW of chilling")
print(f"    the back of house gets HOTTER by {Q_rej:.2f} kW")
print()
print(f"  SUMMER: shop AC must remove that {W_el:.2f} kW -> +{W_el/3.0:.2f} kW more electricity")
print(f"  WINTER: that same {W_el:.2f} kW offsets the heating -> the 'waste' is RECOVERED")
