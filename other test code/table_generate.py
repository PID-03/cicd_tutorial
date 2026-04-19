import json
import logging
from decimal import Decimal, ROUND_HALF_UP, getcontext
from models.static_data import IFDData
from run import create_app


# ==========================================================
# DECIMAL CONFIGURATION
# ==========================================================
getcontext().prec = 28


def D(value):
    return Decimal(str(value))


# ==========================================================
# LOGGING
# ==========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ==========================================================
# STANDARD DURATIONS
# ==========================================================
DURATIONS = [
    1, 2, 3, 4, 5, 10, 15, 20,
    25, 30, 45, 60, 90, 120,
    180, 270, 360, 540,
    720, 1080, 1440, 1800,
    2160, 2880, 4320, 5760,
    7200, 8640, 10080
]


# ==========================================================
# MAIN FUNCTION
# ==========================================================
def generate_graph_output(
    aep_percentage,
    max_storm_duration_min,
    climate_factor,
    catchment_area_m2,
    infiltration_rate_m_per_day,
    orifice_flow_lps,
    tank_length_m,
    tank_width_m,
    max_infiltration_depth_m,
    sidewall_enabled,
    soakwells
):

    logger.info(f"Fetching IFD data for AEP = {aep_percentage}%")

    rows = (
        IFDData.query
        .filter(IFDData.aep_percentage == aep_percentage)
        .order_by(IFDData.duration_minutes.asc())
        .all()
    )

    if not rows:
        raise ValueError(f"No IFD data found for AEP {aep_percentage}%")

    intensity_map = {
        row.duration_minutes: D(row.intensity)
        for row in rows
    }

    # Convert inputs
    climate_factor = D(climate_factor)
    catchment_area_m2 = D(catchment_area_m2)
    infiltration_rate_m_per_day = D(infiltration_rate_m_per_day)
    orifice_flow_lps = D(orifice_flow_lps)
    tank_length_m = D(tank_length_m)
    tank_width_m = D(tank_width_m)
    max_infiltration_depth_m = D(max_infiltration_depth_m)

    infiltration_rate_m_per_hr = infiltration_rate_m_per_day / D("24")
    orifice_flow_m3_per_hr = (orifice_flow_lps / D("1000")) * D("3600")

    tank_base_area = tank_length_m * tank_width_m

    INFO_TABLE = {
        "Ø1800x1500": D("0.031416"),
        "Ø1800x1800": D("0.031416"),
        "Ø1500x1500": D("0.031416"),
        "Ø1200x1200": D("0.013273"),
    }

    soakwell_area = D("0")
    for sw in soakwells:
        soakwell_area += INFO_TABLE[sw["size"]] * D(sw["quantity"])

    # Graph lists
    minutes_list = []
    mm_per_min_list = []
    inflow_list = []
    drainage_list = []
    orifice_list = []
    net_volume_list = []
    infiltration_area_list = []
    emptying_hours_list = []

    # ==========================================================
    # CALCULATION LOOP
    # ==========================================================
    for duration_min in DURATIONS:

        if duration_min > max_storm_duration_min:
            continue

        if duration_min not in intensity_map:
            continue

        duration = D(duration_min)
        duration_hr = duration / D("60")

        intensity_hr = intensity_map[duration_min]
        adjusted_intensity = intensity_hr * (D("1") + climate_factor)

        # INFLOW
        inflow_m3 = (
            (adjusted_intensity / D("1000"))
            * catchment_area_m2
            * duration_hr
        )

        inflow_l = (inflow_m3 * D("1000")).quantize(D("1"), ROUND_HALF_UP)

        mm_per_min = (
            adjusted_intensity / D("60")
        ).quantize(D("0.001"), ROUND_HALF_UP)

        # WATER DEPTH
        water_depth = (inflow_l / D("1000")) / tank_base_area
        effective_depth = min(water_depth, max_infiltration_depth_m)

        # INFILTRATION AREA
        sidewall_area = D("0")
        if sidewall_enabled:
            sidewall_area = (tank_length_m + tank_width_m) * effective_depth

        total_infiltration_area = (
            soakwell_area + tank_base_area + sidewall_area
        ).quantize(D("0.01"), ROUND_HALF_UP)

        # DRAINAGE
        drainage_m3 = (
            infiltration_rate_m_per_hr
            * total_infiltration_area
            * duration_hr
        )

        drainage_l = min(drainage_m3 * D("1000"), inflow_l)
        drainage_l = drainage_l.quantize(D("1"), ROUND_HALF_UP)

        # ORIFICE
        orifice_m3 = orifice_flow_m3_per_hr * duration_hr
        orifice_l = min(orifice_m3 * D("1000"), inflow_l - drainage_l)
        orifice_l = orifice_l.quantize(D("1"), ROUND_HALF_UP)

        # NET VOLUME (litres)
        net_volume_l = max(inflow_l - drainage_l - orifice_l, D("0"))
        net_volume_l = net_volume_l.quantize(D("1"), ROUND_HALF_UP)

        # EMPTYING TIME
        total_outflow_rate = (
            infiltration_rate_m_per_hr * total_infiltration_area
            + orifice_flow_m3_per_hr
        )

        emptying_time_hr = (
            (net_volume_l / D("1000")) / total_outflow_rate
            if total_outflow_rate > 0 else D("0")
        ).quantize(D("0.01"), ROUND_HALF_UP)

        # Append graph values
        minutes_list.append(duration_min)
        mm_per_min_list.append(float(mm_per_min))
        inflow_list.append(float(inflow_l))
        drainage_list.append(float(drainage_l))
        orifice_list.append(float(orifice_l))
        net_volume_list.append(float(net_volume_l))
        infiltration_area_list.append(float(total_infiltration_area))
        emptying_hours_list.append(float(emptying_time_hr))

    # ==========================================================
    # DESIGN VALUES (AS YOU REQUESTED)
    # ==========================================================
    max_infiltration_area = max(infiltration_area_list) if infiltration_area_list else 0
    max_volume_required_m3 = (
        max(net_volume_list) / 1000 if net_volume_list else 0
    )

    return {
        "design": {
            "stormwater_height_m": max_infiltration_area,
            "volume_required_m3": max_volume_required_m3
        },
        "graph": {
            "minutes": minutes_list,
            "mm_per_min": mm_per_min_list,
            "inflow_l": inflow_list,
            "drainage_l": drainage_list,
            "orifice_l": orifice_list,
            "net_volume_l": net_volume_list,
            "infiltration_area_m2": infiltration_area_list,
            "emptying_hours": emptying_hours_list
        }
    }


# ==========================================================
# RUN
# ==========================================================
if __name__ == "__main__":

    app = create_app()

    with app.app_context():

        result = generate_graph_output(
            aep_percentage=10,
            max_storm_duration_min=20,
            climate_factor=0.0,
            catchment_area_m2=7230.7,
            infiltration_rate_m_per_day=10,
            orifice_flow_lps=0,
            tank_length_m=13,
            tank_width_m=12.135,
            max_infiltration_depth_m=1.530,
            sidewall_enabled=True,
            soakwells=[
                {"size": "Ø1800x1500", "quantity": 1},
                {"size": "Ø1800x1500", "quantity": 4},
            ]
        )

        print(json.dumps(result, indent=4))
