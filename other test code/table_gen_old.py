# import math
# from models.static_data import IFDData
# from run import create_app

# DURATIONS = [
#     1, 2, 3, 4, 5, 10, 15, 20, 25, 30,
#     45, 60, 90, 120, 180, 270, 360, 540,
#     720, 1080, 1440, 1800, 2160, 2880,
#     4320, 5760, 7200, 8640, 10080
# ]

# def excel_round(value, digits=0):
#     factor = 10 ** digits
#     if value >= 0:
#         return math.floor(value * factor + 0.5) / factor
#     else:
#         return math.ceil(value * factor - 0.5) / factor
    

# def generate_excel_style_table(
#     aep_percentage,
#     max_storm_duration_min,
#     climate_factor,
#     catchment_area_m2,
#     infiltration_rate_m_per_day,
#     orifice_flow_lps,
#     tank_length_m,
#     tank_width_m,
#     max_infiltration_depth_m,
#     sidewall_enabled,
#     soakwells
# ):

#     rows = (
#         IFDData.query
#         .filter(IFDData.aep_percentage == aep_percentage)
#         .order_by(IFDData.duration_minutes.asc())
#         .all()
#     )
#     print("Fetched Intensities:")
#     for row in rows:
#         print(f"{row.duration_minutes} min -> {float(row.intensity)}")

#         if not rows:
#             raise ValueError(f"No IFD data found for AEP {aep_percentage}%")
    
    

#     intensity_map = {
#         row.duration_minutes: float(row.intensity)
#         for row in rows
#     }

#     # -------------------------------------------------------
#     # INFILTRATION LOOKUP TABLE
#     # -------------------------------------------------------

#     INFO_TABLE = {
#         "Ø1800x1500": 0.031416,
#         "Ø1800x1800": 0.031416,
#         "Ø1500x1500": 0.031416,
#         "Ø1200x1200": 0.013273,
#     }

#     infiltration_rate_m_per_hr = infiltration_rate_m_per_day / 24
#     orifice_flow_m3_per_hr = (orifice_flow_lps / 1000) * 3600

#     # -------------------------------------------------------
#     # SOAKWELL AREA
#     # -------------------------------------------------------

#     soakwell_area = 0
#     for size, qty in soakwells:
#         if size not in INFO_TABLE:
#             raise ValueError(f"Unknown soakwell size: {size}")
#         soakwell_area += INFO_TABLE[size] * qty

#     tank_base_area = tank_length_m * tank_width_m

#     print("\n" + "=" * 170)
#     print(f"STORMWATER CALCULATION TABLE (AEP = {aep_percentage}%)")
#     print("=" * 170)

#     print(f"{'Minutes Selected':<18}"
#           f"{'mm/min (i)':<12}"
#           f"{'Inflow (L)':<15}"
#           f"{'Drainage (L)':<15}"
#           f"{'Orifice (L)':<15}"
#           f"{'Net Volume (L)':<18}"
#           f"{'Infiltration Area (m²)':<25}"
#           f"{'Emptying Time (hrs)':<20}")

#     print("-" * 170)

#     max_storage = 0

#     # ==========================================================
#     # MAIN LOOP (Excel Logic)
#     # ==========================================================

#     for duration in DURATIONS:

#         if duration > max_storm_duration_min:
#             continue

#         if duration not in intensity_map:
#             raise ValueError(f"Missing intensity for {duration} min")
        
        

#         intensity_hr = intensity_map[duration]
#         duration_hr = duration / 60

#         adjusted_intensity = intensity_hr * (1 + climate_factor)
#         intensity_mm_min = adjusted_intensity / 60

#         inflow_m3 = (
#             (adjusted_intensity / 1000)
#             * catchment_area_m2
#             * duration_hr
#         )

#         inflow_l = inflow_m3 * 1000

#         water_depth = (inflow_l / 1000) / tank_base_area
#         effective_depth = min(water_depth, max_infiltration_depth_m)

#         sidewall_area = 0
#         if sidewall_enabled:
#             sidewall_area = (tank_length_m + tank_width_m) * effective_depth

#         total_infiltration_area = soakwell_area + tank_base_area + sidewall_area

#         drainage_m3 = (
#             infiltration_rate_m_per_hr
#             * total_infiltration_area
#             * duration_hr
#         )

#         drainage_l = min(drainage_m3 * 1000, inflow_l)

#         orifice_m3 = orifice_flow_m3_per_hr * duration_hr
#         orifice_l = min(orifice_m3 * 1000, inflow_l - drainage_l)

#         net_volume = max(inflow_l - drainage_l - orifice_l, 0)

#         max_storage = max(max_storage, net_volume)

#         total_outflow_rate = (
#             infiltration_rate_m_per_hr * total_infiltration_area
#             + orifice_flow_m3_per_hr
#         )

#         emptying_time = (
#             (net_volume / 1000) / total_outflow_rate
#             if total_outflow_rate > 0 else 0
#         )

#         print(f"{duration:<18}"
#               f"{excel_round(intensity_mm_min,3):<12}"
#               f"{excel_round(inflow_l,0):<15}"
#               f"{excel_round(drainage_l,0):<15}"
#               f"{excel_round(orifice_l,0):<15}"
#               f"{excel_round(net_volume,0):<18}"
#               f"{excel_round(total_infiltration_area,2):<25}"
#               f"{excel_round(emptying_time,2):<20}")

#     print("-" * 170)
#     print(f"Required Storage Volume = {excel_round(max_storage/1000,2)} m³")
#     print("=" * 170)


# # ==========================================================
# # RUN
# # ==========================================================

# if __name__ == "__main__":

#     app = create_app()

#     with app.app_context():
#         generate_excel_style_table(
#             aep_percentage=10,
#             max_storm_duration_min=10080,
#             climate_factor=0.0,
#             catchment_area_m2=7231,
#             infiltration_rate_m_per_day=10,
#             orifice_flow_lps=0,
#             tank_length_m=13,
#             tank_width_m=12.135,
#             max_infiltration_depth_m=1.530,
#             sidewall_enabled=True,
#             soakwells=[
#                 ("Ø1800x1500", 4),
#                 ("Ø1800x1500", 1),
#             ]
#         )



import logging
from decimal import Decimal, ROUND_HALF_UP, getcontext
from models.static_data import IFDData
from run import create_app

# ==========================================================
# DECIMAL CONFIGURATION
# ==========================================================
getcontext().prec = 28  # High precision for hydraulic calculations

def D(value):
    """Safe Decimal conversion"""
    return Decimal(str(value))


# ==========================================================
# LOGGING CONFIGURATION
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
    1, 2, 3, 4, 5, 10, 15, 20, 25, 30,
    45, 60, 90, 120, 180, 270, 360, 540,
    720, 1080, 1440, 1800, 2160, 2880,
    4320, 5760, 7200, 8640, 10080
]


# ==========================================================
# MAIN FUNCTION
# ==========================================================
def generate_excel_style_table(
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

    # Build intensity map (full precision from DB)
    intensity_map = {
        row.duration_minutes: D(row.intensity)
        for row in rows
    }

    # ==========================================================
    # CONVERT ALL INPUTS TO DECIMAL
    # ==========================================================
    climate_factor = D(climate_factor)
    catchment_area_m2 = D(catchment_area_m2)
    infiltration_rate_m_per_day = D(infiltration_rate_m_per_day)
    orifice_flow_lps = D(orifice_flow_lps)
    tank_length_m = D(tank_length_m)
    tank_width_m = D(tank_width_m)
    max_infiltration_depth_m = D(max_infiltration_depth_m)

    infiltration_rate_m_per_hr = infiltration_rate_m_per_day / D("24")
    orifice_flow_m3_per_hr = (orifice_flow_lps / D("1000")) * D("3600")

    # ==========================================================
    # INFILTRATION LOOKUP TABLE
    # ==========================================================
    INFO_TABLE = {
        "Ø1800x1500": D("0.031416"),
        "Ø1800x1800": D("0.031416"),
        "Ø1500x1500": D("0.031416"),
        "Ø1200x1200": D("0.013273"),
    }

    soakwell_area = D("0")
    for size, qty in soakwells:
        if size not in INFO_TABLE:
            raise ValueError(f"Unknown soakwell size: {size}")
        soakwell_area += INFO_TABLE[size] * D(qty)

    tank_base_area = tank_length_m * tank_width_m

    print("\n" + "=" * 170)
    print(f"STORMWATER CALCULATION TABLE (AEP = {aep_percentage}%)")
    print("=" * 170)

    print(f"{'Minutes':<10}"
          f"{'mm/min':<12}"
          f"{'Inflow (L)':<15}"
          f"{'Drainage (L)':<15}"
          f"{'Orifice (L)':<15}"
          f"{'Net Volume (L)':<18}"
          f"{'Infiltration Area':<20}"
          f"{'Emptying (hrs)':<15}")

    print("-" * 170)

    max_storage = D("0")

    # ==========================================================
    # MAIN LOOP
    # ==========================================================
    for duration in DURATIONS:

        if duration > max_storm_duration_min:
            continue

        duration = D(duration)

        intensity_hr = intensity_map[int(duration)]

        # Full precision intensity
        adjusted_intensity = intensity_hr * (D("1") + climate_factor)

        duration_hr = duration / D("60")

        # ------------------------------------------------------
        # INFLOW (FULL PRECISION)
        # ------------------------------------------------------
        inflow_m3 = (
            (adjusted_intensity / D("1000"))
            * catchment_area_m2
            * duration_hr
        )

        inflow_l = inflow_m3 * D("1000")

        # Rounded only for display
        inflow_display = inflow_l.quantize(D("1"), rounding=ROUND_HALF_UP)

        # Display mm/min (rounded only for printing)
        intensity_mm_min_display = (
            adjusted_intensity / D("60")
        ).quantize(D("0.001"), rounding=ROUND_HALF_UP)

        # ------------------------------------------------------
        # STORAGE + INFILTRATION
        # ------------------------------------------------------
        water_depth = (inflow_l / D("1000")) / tank_base_area
        effective_depth = min(water_depth, max_infiltration_depth_m)

        sidewall_area = D("0")
        if sidewall_enabled:
            sidewall_area = (tank_length_m + tank_width_m) * effective_depth

        total_infiltration_area = (
            soakwell_area + tank_base_area + sidewall_area
        ).quantize(D("0.01"), rounding=ROUND_HALF_UP)

        drainage_m3 = (
            infiltration_rate_m_per_hr
            * total_infiltration_area
            * duration_hr
        )

        drainage_l = min(drainage_m3 * D("1000"), inflow_l)
        drainage_l = drainage_l.quantize(D("1"), rounding=ROUND_HALF_UP)

        orifice_m3 = orifice_flow_m3_per_hr * duration_hr
        orifice_l = min(orifice_m3 * D("1000"), inflow_l - drainage_l)
        orifice_l = orifice_l.quantize(D("1"), rounding=ROUND_HALF_UP)

        net_volume = max(inflow_l - drainage_l - orifice_l, D("0"))
        net_volume = net_volume.quantize(D("1"), rounding=ROUND_HALF_UP)

        max_storage = max(max_storage, net_volume)

        total_outflow_rate = (
            infiltration_rate_m_per_hr * total_infiltration_area
            + orifice_flow_m3_per_hr
        )

        emptying_time = (
            (net_volume / D("1000")) / total_outflow_rate
            if total_outflow_rate > 0 else D("0")
        ).quantize(D("0.01"), rounding=ROUND_HALF_UP)

        print(f"{int(duration):<10}"
              f"{intensity_mm_min_display:<12}"
              f"{inflow_display:<15}"
              f"{drainage_l:<15}"
              f"{orifice_l:<15}"
              f"{net_volume:<18}"
              f"{total_infiltration_area:<20}"
              f"{emptying_time:<15}")

    print("-" * 170)
    print(f"Required Storage Volume = {(max_storage / D('1000')).quantize(D('0.01'))} m³")
    print("=" * 170)


# ==========================================================
# RUN
# ==========================================================
if __name__ == "__main__":

    app = create_app()

    with app.app_context():
        generate_excel_style_table(
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
                ("Ø1800x1500", 4),
                ("Ø1800x1500", 1),
            ]
        )