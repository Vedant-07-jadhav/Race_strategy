"""F1 Race Timing Tower Display.

Renders an authentic, live-updating Formula 1 style timing tower in the terminal
showing positions, interval deltas, tire compounds, tire ages, and pit stop status.
"""

from typing import Dict, List, Optional


def render_timing_tower(
    lap: int,
    total_laps: int,
    car_times: Dict[str, float],
    car_tire_ages: Dict[str, float],
    car_compounds: Optional[Dict[str, str]] = None,
    pit_counts: Optional[Dict[str, int]] = None,
    safety_car_status: int = 0,
    top_n: int = 22,
) -> str:
    """Format and return a string representing the race timing tower at a given lap."""
    car_compounds = car_compounds or {}
    pit_counts = pit_counts or {}

    # Sort drivers by total race time
    sorted_cars = sorted(car_times.items(), key=lambda x: x[1])
    leader_time = sorted_cars[0][1] if sorted_cars else 0.0

    # Safety car banner
    sc_banner = "GREEN FLAG"
    if safety_car_status == 1:
        sc_banner = "🟡 VIRTUAL SAFETY CAR (VSC) DEPLOYED"
    elif safety_car_status == 2:
        sc_banner = "🟠 FULL SAFETY CAR (SC) DEPLOYED — PACK BUNCHED"

    header = [
        f"{'='*86}",
        f"🏁 F1 TIMING TOWER — LAP {lap}/{total_laps} | STATUS: {sc_banner}",
        f"{'='*86}",
        f"{'POS':<4} | {'DRIVER':<18} | {'GAP TO P1':<12} | {'INTERVAL':<10} | {'TIRE':<8} | {'PITS':<5} | {'STATUS':<14}",
        f"{'-'*86}",
    ]

    lines = list(header)
    prev_time = leader_time

    for i, (driver, time_val) in enumerate(sorted_cars[:top_n]):
        pos = i + 1
        if i == 0:
            gap_str = "LEADER"
            interval_str = "  —   "
        else:
            gap = time_val - leader_time
            interval = time_val - prev_time
            gap_str = f"+{gap:6.3f}s"
            interval_str = f"+{interval:6.3f}s"

        prev_time = time_val

        age = int(round(car_tire_ages.get(driver, 0.0)))
        compound_raw = car_compounds.get(driver, "Soft")
        comp_badge = f"[{compound_raw[0]}] ({age:2d})"
        pits = pit_counts.get(driver, 0)

        status_str = "RACING"
        if safety_car_status == 1:
            status_str = "VSC DELTA"
        elif safety_car_status == 2:
            status_str = "SC TRAIN"
        elif age > 20:
            status_str = "HIGH DEG"

        lines.append(
            f"{pos:3d}  | {driver:<18} | {gap_str:<12} | {interval_str:<10} | {comp_badge:<8} | {pits:4d}  | {status_str:<14}"
        )

    lines.append(f"{'='*86}\n")
    return "\n".join(lines)
