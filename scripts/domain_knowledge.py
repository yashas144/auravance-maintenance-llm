"""
Domain knowledge base for synthetic training data generation.

This encodes realistic relationships between equipment types, failure modes,
and telemetry signatures — the kind of domain logic a reliability engineer
would use. Synthetic generation from structured domain rules (rather than
pure LLM freeform generation) keeps the dataset grounded and makes failure
modes physically plausible, which matters for eval quality later.
"""

import random

# Equipment types and their plausible failure modes with root causes
EQUIPMENT_PROFILES = {
    "centrifugal_pump": {
        "sensors": ["vibration_mm_s", "bearing_temp_c", "flow_rate_pct", "discharge_pressure_bar"],
        "failure_modes": {
            "bearing_wear": {
                "root_cause": "Progressive bearing degradation due to lubrication breakdown or contamination",
                "signature": {"vibration_mm_s": (4.5, 9.0), "bearing_temp_c": (75, 95)},
                "action": "Schedule bearing inspection and replace lubricant; monitor vibration trend daily",
            },
            "cavitation": {
                "root_cause": "Insufficient net positive suction head causing vapor bubble collapse at impeller",
                "signature": {"vibration_mm_s": (3.0, 6.0), "flow_rate_pct": (40, 65)},
                "action": "Inspect suction line for blockage or air ingress; verify NPSH margin",
            },
            "impeller_imbalance": {
                "root_cause": "Impeller wear or debris buildup causing rotational imbalance",
                "signature": {"vibration_mm_s": (5.0, 10.0), "discharge_pressure_bar": (2.5, 4.0)},
                "action": "Inspect impeller for erosion or fouling; rebalance or replace",
            },
        },
    },
    "conveyor_motor": {
        "sensors": ["current_draw_a", "winding_temp_c", "rpm", "vibration_mm_s"],
        "failure_modes": {
            "winding_insulation_degradation": {
                "root_cause": "Thermal cycling has degraded stator winding insulation, increasing leakage current",
                "signature": {"winding_temp_c": (95, 130), "current_draw_a": (18, 26)},
                "action": "Perform insulation resistance test; plan motor rewind or replacement within 2 weeks",
            },
            "belt_misalignment": {
                "root_cause": "Drive belt misalignment causing uneven load and elevated vibration",
                "signature": {"vibration_mm_s": (4.0, 8.0), "rpm": (1150, 1350)},
                "action": "Inspect and realign belt drive; check pulley wear",
            },
            "bearing_fatigue": {
                "root_cause": "Rolling element bearing fatigue from cumulative load cycles",
                "signature": {"vibration_mm_s": (5.5, 11.0), "current_draw_a": (15, 20)},
                "action": "Replace motor bearings at next planned downtime window",
            },
        },
    },
    "gearbox": {
        "sensors": ["oil_temp_c", "vibration_mm_s", "oil_particle_count_ppm", "output_rpm"],
        "failure_modes": {
            "gear_tooth_wear": {
                "root_cause": "Surface fatigue on gear teeth from prolonged high-load operation",
                "signature": {"vibration_mm_s": (6.0, 12.0), "oil_particle_count_ppm": (150, 400)},
                "action": "Perform oil analysis and borescope inspection of gear mesh",
            },
            "oil_contamination": {
                "root_cause": "Water or particulate contamination degrading lubricant film strength",
                "signature": {"oil_temp_c": (70, 90), "oil_particle_count_ppm": (300, 600)},
                "action": "Drain and replace gearbox oil; inspect seals for ingress point",
            },
        },
    },
    "hvac_compressor": {
        "sensors": ["suction_pressure_bar", "discharge_temp_c", "current_draw_a", "vibration_mm_s"],
        "failure_modes": {
            "refrigerant_undercharge": {
                "root_cause": "Refrigerant leak causing reduced suction pressure and inefficient cooling",
                "signature": {"suction_pressure_bar": (1.5, 2.8), "discharge_temp_c": (95, 115)},
                "action": "Leak-test refrigerant circuit and recharge to spec",
            },
            "valve_leakage": {
                "root_cause": "Worn compressor valve plates causing internal gas bypass",
                "signature": {"discharge_temp_c": (100, 125), "current_draw_a": (20, 28)},
                "action": "Inspect and replace suction/discharge valve plates",
            },
        },
    },
    "conveyor_belt": {
        "sensors": ["belt_tension_pct", "vibration_mm_s", "motor_current_a", "tracking_deviation_mm"],
        "failure_modes": {
            "belt_slippage": {
                "root_cause": "Reduced belt tension causing slip at the drive pulley under load",
                "signature": {"belt_tension_pct": (55, 75), "motor_current_a": (14, 19)},
                "action": "Re-tension belt and inspect pulley lagging for wear",
            },
            "tracking_misalignment": {
                "root_cause": "Progressive belt drift due to idler misalignment or uneven loading",
                "signature": {"tracking_deviation_mm": (25, 60), "vibration_mm_s": (2.5, 5.0)},
                "action": "Adjust idler alignment and inspect load distribution",
            },
        },
    },
}

SENSOR_DISPLAY = {
    "vibration_mm_s": "vibration (mm/s)",
    "bearing_temp_c": "bearing temp (°C)",
    "flow_rate_pct": "flow rate (%)",
    "discharge_pressure_bar": "discharge pressure (bar)",
    "current_draw_a": "current draw (A)",
    "winding_temp_c": "winding temp (°C)",
    "rpm": "RPM",
    "oil_temp_c": "oil temp (°C)",
    "oil_particle_count_ppm": "oil particle count (ppm)",
    "output_rpm": "output RPM",
    "suction_pressure_bar": "suction pressure (bar)",
    "discharge_temp_c": "discharge temp (°C)",
    "belt_tension_pct": "belt tension (%)",
    "tracking_deviation_mm": "tracking deviation (mm)",
    "motor_current_a": "motor current (A)",
}

NORMAL_RANGES = {
    "vibration_mm_s": (0.5, 2.5),
    "bearing_temp_c": (40, 60),
    "flow_rate_pct": (85, 100),
    "discharge_pressure_bar": (5.0, 6.5),
    "current_draw_a": (8, 12),
    "winding_temp_c": (55, 75),
    "rpm": (1450, 1480),
    "oil_temp_c": (45, 60),
    "oil_particle_count_ppm": (20, 60),
    "output_rpm": (290, 310),
    "suction_pressure_bar": (3.5, 4.5),
    "discharge_temp_c": (60, 80),
    "belt_tension_pct": (90, 100),
    "tracking_deviation_mm": (0, 5),
    "motor_current_a": (9, 12),
}


def sample_value(sensor: str, anomalous_range: tuple = None) -> float:
    lo, hi = anomalous_range if anomalous_range else NORMAL_RANGES[sensor]
    return round(random.uniform(lo, hi), 1)
