from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
WORK = ROOT / "_work"
WORK.mkdir(parents=True, exist_ok=True)


P = {
    "g": 9.81,
    "bearing_mass_kg": 3032.0,
    "design_mobile_mass_kg": 3500.0,
    "bearing_od_mm": 1420.0,
    "bearing_id_mm": 900.0,
    "bearing_width_mm": 515.0,
    "bearing_bottom_z_mm": 890.0,
    "bearing_cg_above_pad_mm": 257.5,
    "pad_r_in_mm": 638.0,
    "pad_r_out_mm": 688.0,
    "pad_sector_deg": 24.0,
    "pad_angles_deg": [0.0, 120.0, 240.0],
    "pad_xy_mm": [[663.0, 0.0], [-331.5, 574.175], [-331.5, -574.175]],
    "placement_requirement_radial_mm": 5.0,
    "horizontal_accel_m_s2": 0.30,
    "vertical_service_factor": 1.15,
    "uls_factor": 1.40,
    "wheel_xy_mm": [[-930.0, -722.0], [-930.0, 722.0], [930.0, -722.0], [930.0, 722.0]],
    "mobile_cg_envelope_x_mm": 100.0,
    "mobile_cg_envelope_y_mm": 100.0,
    "wheel_catalog_dynamic_kg": 2500.0,
    "rail_y_min_mm": -4620.0,
    "rail_y_max_mm": 1920.0,
    "rail_support_count": 12,
    "table_center_load_y_mm": -3320.038,
    "table_center_wash_y_mm": 0.0,
    "rail_scan_step_mm": 5.0,
    "rail_E_MPa": 200000.0,
    "rail_I_mm4": 900000.0,
    "rail_Z_head_mm3": 27000.0,
    "rail_Z_base_mm3": 41500.0,
    "rail_mass_kg_m": 22.10,
    "center_force_required_N": 2000.0,
    "retention_force_required_N": 2000.0,
    "handle_design_force_N": 1500.0,
    "steel_density_kg_mm3": 7.85e-6,
    "steel_E_MPa": 200000.0,
    "steel_Fy_candidate_MPa": 355.0,
}


def pad_coverage_fraction(dx: float, dy: float, pad_angle_deg: float, step_deg: float = 0.10) -> float:
    """Area of fixed annular PAD covered by the displaced bearing annulus.

    For the evaluated displacement range (<= 150 mm), the PAD remains outside the
    bearing bore, so the inner circle does not truncate the PAD. The outer-circle
    intersection is integrated by midpoint quadrature along the 24 degree sector.
    """
    r1, r2 = P["pad_r_in_mm"], P["pad_r_out_mm"]
    ro = P["bearing_od_mm"] / 2.0
    half = P["pad_sector_deg"] / 2.0
    n = max(1, int(round(P["pad_sector_deg"] / step_deg)))
    dtheta = math.radians(P["pad_sector_deg"] / n)
    area = 0.0
    for j in range(n):
        theta = math.radians(pad_angle_deg - half + (j + 0.5) * P["pad_sector_deg"] / n)
        c, s = math.cos(theta), math.sin(theta)
        proj = dx * c + dy * s
        perp = dx * s - dy * c
        disc = ro * ro - perp * perp
        if disc <= 0.0:
            continue
        root = math.sqrt(disc)
        low = max(r1, proj - root)
        high = min(r2, proj + root)
        if high > low:
            area += 0.5 * (high * high - low * low) * dtheta
    full = 0.5 * (r2 * r2 - r1 * r1) * math.radians(P["pad_sector_deg"])
    return max(0.0, min(1.0, area / full))


def solve_reactions(points: list[list[float]], total_kN: float, ex_mm: float, ey_mm: float) -> np.ndarray:
    pts = np.asarray(points, dtype=float)
    a = np.vstack([np.ones(len(pts)), pts[:, 0], pts[:, 1]])
    rhs = np.array([total_kN, total_kN * ex_mm, total_kN * ey_mm], dtype=float)
    if len(pts) == 3:
        return np.linalg.solve(a, rhs)
    raise ValueError("solve_reactions is used for three-point support only")


def wheel_cases() -> list[dict]:
    w_kN = P["design_mobile_mass_kg"] * P["g"] / 1000.0
    ex0, ey0 = P["mobile_cg_envelope_x_mm"], P["mobile_cg_envelope_y_mm"]
    wheels = P["wheel_xy_mm"]
    cases: list[dict] = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            ex, ey = sx * ex0, sy * ey0
            reactions = []
            for x, y in wheels:
                reactions.append(w_kN / 4.0 * (1.0 + x * ex / (930.0**2)) * (1.0 + y * ey / (722.0**2)))
            cases.append({
                "case": f"4C_{'P' if sx > 0 else 'M'}{'P' if sy > 0 else 'M'}",
                "contacts": 4,
                "missing": "-",
                "ex_mm": ex,
                "ey_mm": ey,
                "reactions_kN": reactions,
                "eligible": min(reactions) >= -1e-9,
            })
    for missing in range(4):
        active_idx = [i for i in range(4) if i != missing]
        active_pts = [wheels[i] for i in active_idx]
        for sx in (-1, 1):
            for sy in (-1, 1):
                ex, ey = sx * ex0, sy * ey0
                r_active = solve_reactions(active_pts, w_kN, ex, ey)
                reactions = [0.0] * 4
                for idx, value in zip(active_idx, r_active):
                    reactions[idx] = float(value)
                eligible = min(r_active) >= -1e-9
                cases.append({
                    "case": f"3C_W{missing + 1}_{'P' if sx > 0 else 'M'}{'P' if sy > 0 else 'M'}",
                    "contacts": 3,
                    "missing": f"W-{missing + 1:02d}",
                    "ex_mm": ex,
                    "ey_mm": ey,
                    "reactions_kN": reactions,
                    "eligible": bool(eligible),
                })
    return cases


def pad_results() -> dict:
    bearing_w_kN = P["bearing_mass_kg"] * P["g"] / 1000.0
    inertia_e = P["horizontal_accel_m_s2"] * P["bearing_cg_above_pad_mm"] / P["g"]
    total_e = P["placement_requirement_radial_mm"] + inertia_e
    reaction_cases = []
    for angle in range(0, 360, 15):
        ex = total_e * math.cos(math.radians(angle))
        ey = total_e * math.sin(math.radians(angle))
        r = solve_reactions(P["pad_xy_mm"], bearing_w_kN, ex, ey)
        reaction_cases.append({
            "case": f"RES_{angle:03d}",
            "angle_deg": angle,
            "resultant_ex_mm": ex,
            "resultant_ey_mm": ey,
            "reactions_kN": [float(x) for x in r],
            "eligible": bool(min(r) >= -1e-9),
        })
    coverage_cases = [{"case": "CENTRADO", "dx_mm": 0.0, "dy_mm": 0.0, "design": True}]
    for angle in range(0, 360, 45):
        coverage_cases.append({
            "case": f"E5_{angle:03d}",
            "dx_mm": P["placement_requirement_radial_mm"] * math.cos(math.radians(angle)),
            "dy_mm": P["placement_requirement_radial_mm"] * math.sin(math.radians(angle)),
            "design": True,
        })
    coverage_cases.append({"case": "AUDIT_M100_P100", "dx_mm": -100.0, "dy_mm": 100.0, "design": False})
    for case in coverage_cases:
        fractions = [pad_coverage_fraction(case["dx_mm"], case["dy_mm"], a) for a in P["pad_angles_deg"]]
        case["coverage_fraction"] = fractions
        case["all_full_contact"] = min(fractions) >= 0.999999
    eligible = [c for c in reaction_cases if c["eligible"]]
    governing = max(eligible, key=lambda c: max(c["reactions_kN"]))
    static_max = max(governing["reactions_kN"])
    full_liner_area = 0.5 * (P["pad_r_out_mm"]**2 - P["pad_r_in_mm"]**2) * math.radians(P["pad_sector_deg"])
    return {
        "bearing_weight_kN": bearing_w_kN,
        "physical_placement_requirement_mm": P["placement_requirement_radial_mm"],
        "outer_full_contact_limit_mm": P["bearing_od_mm"] / 2.0 - P["pad_r_out_mm"],
        "geometric_margin_at_requirement_mm": P["bearing_od_mm"] / 2.0 - P["pad_r_out_mm"] - P["placement_requirement_radial_mm"],
        "inertial_equivalent_mm": inertia_e,
        "combined_resultant_envelope_mm": total_e,
        "coverage_cases": coverage_cases,
        "reaction_cases": reaction_cases,
        "governing_case": governing["case"],
        "max_unfactored_kN": static_max,
        "service_kN": static_max * P["vertical_service_factor"],
        "uls_kN": static_max * P["uls_factor"],
        "full_liner_area_mm2": full_liner_area,
        "service_pressure_MPa": static_max * P["vertical_service_factor"] * 1000.0 / full_liner_area,
        "uls_pressure_MPa": static_max * P["uls_factor"] * 1000.0 / full_liner_area,
    }


def adjacent_support_reactions(loads: list[tuple[float, float]], supports: np.ndarray) -> np.ndarray:
    reactions = np.zeros(len(supports))
    for y, load_kN in loads:
        if y <= supports[0]:
            reactions[0] += load_kN
            continue
        if y >= supports[-1]:
            reactions[-1] += load_kN
            continue
        j = int(np.searchsorted(supports, y) - 1)
        length = supports[j + 1] - supports[j]
        xi = (y - supports[j]) / length
        reactions[j] += load_kN * (1.0 - xi)
        reactions[j + 1] += load_kN * xi
    return reactions


def beam_reactions(loads: list[tuple[float, float]], supports: np.ndarray, e_mod: float, inertia: float) -> np.ndarray:
    n = len(supports)
    ndof = 2 * n
    k = np.zeros((ndof, ndof))
    f = np.zeros(ndof)
    for e in range(n - 1):
        length = supports[e + 1] - supports[e]
        c = e_mod * inertia / length**3
        ke = c * np.array([
            [12, 6 * length, -12, 6 * length],
            [6 * length, 4 * length**2, -6 * length, 2 * length**2],
            [-12, -6 * length, 12, -6 * length],
            [6 * length, 2 * length**2, -6 * length, 4 * length**2],
        ])
        dof = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        k[np.ix_(dof, dof)] += ke
    for y, load_kN in loads:
        y = min(max(y, supports[0]), supports[-1])
        if abs(y - supports[-1]) < 1e-9:
            f[2 * (n - 1)] -= load_kN * 1000.0
            continue
        e = int(np.searchsorted(supports, y, side="right") - 1)
        e = min(max(e, 0), n - 2)
        length = supports[e + 1] - supports[e]
        xi = (y - supports[e]) / length
        shape = np.array([
            1 - 3 * xi**2 + 2 * xi**3,
            length * (xi - 2 * xi**2 + xi**3),
            3 * xi**2 - 2 * xi**3,
            length * (-xi**2 + xi**3),
        ])
        dof = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        f[dof] -= load_kN * 1000.0 * shape
    fixed = np.array([2 * i for i in range(n)], dtype=int)
    free = np.array([2 * i + 1 for i in range(n)], dtype=int)
    u = np.zeros(ndof)
    u[free] = np.linalg.solve(k[np.ix_(free, free)], f[free])
    reaction_n = k @ u - f
    return reaction_n[fixed] / 1000.0


def rail_envelope(wheel_case_rows: list[dict], support_count: int | None = None) -> dict:
    count = int(P["rail_support_count"] if support_count is None else support_count)
    supports = np.linspace(P["rail_y_min_mm"], P["rail_y_max_mm"], count)
    centers = np.arange(P["table_center_load_y_mm"], P["table_center_wash_y_mm"] + 0.5 * P["rail_scan_step_mm"], P["rail_scan_step_mm"])
    if centers[-1] < P["table_center_wash_y_mm"] - 1e-9:
        centers = np.append(centers, P["table_center_wash_y_mm"])
    max_adj = np.full(len(supports), -np.inf)
    min_fe = np.full(len(supports), np.inf)
    max_fe = np.full(len(supports), -np.inf)
    gov_adj = None
    gov_fe = None
    max_adj_global = -np.inf
    max_fe_global = -np.inf
    for case in wheel_case_rows:
        if not case["eligible"]:
            continue
        uls = [r * P["uls_factor"] for r in case["reactions_kN"]]
        for center in centers:
            for side, idx in (("L", (0, 1)), ("R", (2, 3))):
                loads = []
                for i in idx:
                    if uls[i] > 1e-9:
                        loads.append((center + P["wheel_xy_mm"][i][1], uls[i]))
                if not loads:
                    continue
                adj = adjacent_support_reactions(loads, supports)
                fe = beam_reactions(loads, supports, P["rail_E_MPa"], P["rail_I_mm4"])
                for j, value in enumerate(adj):
                    if value > max_adj[j]:
                        max_adj[j] = value
                    if value > max_adj_global:
                        max_adj_global = value
                        gov_adj = {"support": j + 1, "value_kN": float(value), "case": case["case"], "side": side, "center_y_mm": float(center), "loads": loads}
                for j, value in enumerate(fe):
                    if value > max_fe[j]:
                        max_fe[j] = value
                    if value > max_fe_global:
                        max_fe_global = value
                        gov_fe = {"support": j + 1, "value_kN": float(value), "case": case["case"], "side": side, "center_y_mm": float(center), "loads": loads}
                    min_fe[j] = min(min_fe[j], value)
    pitch = supports[1] - supports[0]
    p_uls = max(max(c["reactions_kN"]) for c in wheel_case_rows if c["eligible"]) * P["uls_factor"]
    p_serv = max(max(c["reactions_kN"]) for c in wheel_case_rows if c["eligible"]) * P["vertical_service_factor"]
    moment_nmm = p_uls * 1000.0 * pitch / 4.0
    return {
        "support_count": count,
        "support_positions_mm": [float(x) for x in supports],
        "support_pitch_mm": float(pitch),
        "scan_positions": int(len(centers)),
        "adjacent_max_by_support_kN": [float(x) for x in max_adj],
        "continuous_max_by_support_kN": [float(x) for x in max_fe],
        "continuous_min_by_support_kN": [float(x) for x in min_fe],
        "governing_adjacent": gov_adj,
        "governing_continuous": gov_fe,
        "governing_vertical_installation_kN": float(max(max(max_adj), max(max_fe))),
        "governing_uplift_continuous_kN": float(min(min_fe)),
        "lateral_installation_kN": float(0.10 * max(max(max_adj), max(max_fe))),
        "simple_span_moment_Nmm": float(moment_nmm),
        "simple_span_head_stress_MPa": float(moment_nmm / P["rail_Z_head_mm3"]),
        "simple_span_base_stress_MPa": float(moment_nmm / P["rail_Z_base_mm3"]),
        "simple_span_service_deflection_mm": float(p_serv * 1000.0 * pitch**3 / (48.0 * P["rail_E_MPa"] * P["rail_I_mm4"])),
        "rail_self_weight_support_kN": float(P["rail_mass_kg_m"] * P["g"] * pitch / 1_000_000.0),
        "note": "Adjacency model is the transparent two-support transfer bound; continuous FE is a sensitivity with vertical supports and free rotations.",
    }


def circular_hollow_properties(od: float, thickness: float) -> tuple[float, float, float]:
    inner = od - 2.0 * thickness
    area = math.pi * (od**2 - inner**2) / 4.0
    inertia = math.pi * (od**4 - inner**4) / 64.0
    section_modulus = inertia / (od / 2.0)
    return area, inertia, section_modulus


def mechanism_results() -> dict:
    e = P["steel_E_MPa"]
    fy = P["steel_Fy_candidate_MPa"]
    # Locator mast: RHS 80 radial x 40 tangential x 6 mm, 195 mm effective height.
    h, b, t, length = 80.0, 40.0, 6.0, 195.0
    i_rhs = (b * h**3 - (b - 2 * t) * (h - 2 * t)**3) / 12.0
    z_rhs = i_rhs / (h / 2.0)
    f_center = P["center_force_required_N"]
    m_center = f_center * length
    mast_stress = m_center / z_rhs
    mast_deflection = f_center * length**3 / (3.0 * e * i_rhs)
    screw_root = 19.0
    screw_area = math.pi * screw_root**2 / 4.0
    screw_stress = f_center / screw_area
    screw_i = math.pi * screw_root**4 / 64.0
    screw_pcr = math.pi**2 * e * screw_i / 430.0**2
    screw_torque = f_center * 5.0 / (2.0 * math.pi * 0.30)
    pin16_tau = f_center / (2.0 * math.pi * 16.0**2 / 4.0)

    # Retention cleat: 2 kN envelope, four vertical M12 fasteners, 180 mm radial rows.
    f_ret = P["retention_force_required_N"]
    ret_lever = 100.0
    ret_moment = f_ret * ret_lever
    ret_contact_pressure = f_ret / (80.0 * 30.0)
    ret_bolt_shear = f_ret / 4.0
    ret_bolt_tension = ret_moment / 180.0 / 2.0
    ret_bolt_resultant = math.hypot(ret_bolt_shear, ret_bolt_tension)
    ret_web_stress = 6.0 * f_ret * 20.0 / (80.0 * 10.0**2)

    # Handle: CHS 42.4 x 3.2, 900 mm bar, 250 mm posts, 1.5 kN total envelope.
    area_chs, i_chs, z_chs = circular_hollow_properties(42.4, 3.2)
    f_handle = P["handle_design_force_N"]
    handle_bar_moment = f_handle * 900.0 / 4.0
    handle_bar_stress = handle_bar_moment / z_chs
    post_force = f_handle / 2.0
    post_moment = post_force * 250.0
    post_stress = post_moment / z_chs
    handle_bolt_shear = post_force / 4.0
    handle_bolt_tension = post_moment / 80.0 / 2.0
    handle_bolt_resultant = math.hypot(handle_bolt_shear, handle_bolt_tension)

    return {
        "locator": {
            "required_force_N": f_center,
            "stroke_mm": 345.0,
            "guide_z_max_mm": 780.0,
            "mast_section": "RHS 80x40x6 S355 candidate",
            "mast_I_mm4": i_rhs,
            "mast_Z_mm3": z_rhs,
            "mast_stress_MPa": mast_stress,
            "mast_deflection_mm": mast_deflection,
            "mast_utilization_0_60Fy": mast_stress / (0.60 * fy),
            "screw": "Tr24x5 candidate, 19 mm assumed root",
            "screw_axial_stress_MPa": screw_stress,
            "screw_Euler_kN": screw_pcr / 1000.0,
            "screw_torque_Nm": screw_torque / 1000.0,
            "lock_pin_d_mm": 16.0,
            "lock_pin_double_shear_MPa": pin16_tau,
            "status": "PREDIMENSIONADO; guide bearings, wear, corrosion and certified hardware pending",
        },
        "retention": {
            "required_force_per_stop_N": f_ret,
            "contact_pressure_MPa": ret_contact_pressure,
            "base_moment_Nmm": ret_moment,
            "bolt_pattern": "4 x M12 candidate, radial rows 180 mm",
            "bolt_shear_each_N": ret_bolt_shear,
            "bolt_tension_each_N": ret_bolt_tension,
            "bolt_resultant_each_N": ret_bolt_resultant,
            "web_strip_stress_MPa": ret_web_stress,
            "status": "LOAD_PATH_DEFINED_AND_PRELIMINARY_CHECKED; final code/material/interface pending",
        },
        "handle": {
            "design_force_total_N": f_handle,
            "section": "CHS 42.4x3.2 candidate",
            "bar_stress_MPa": handle_bar_stress,
            "post_stress_MPa": post_stress,
            "connection": "2 end plates; 4 x M12 candidate per post through end-beam web",
            "bolt_shear_each_N": handle_bolt_shear,
            "bolt_tension_each_N": handle_bolt_tension,
            "bolt_resultant_each_N": handle_bolt_resultant,
            "status": "GEOMETRY_AND_LOAD_PATH_DEFINED; ergonomic test and final connection code pending",
        },
    }


def volume_mass(boxes: list[tuple[float, float, float]], cylinders: list[tuple[float, float]] = []) -> float:
    volume = sum(a * b * c for a, b, c in boxes)
    volume += sum(math.pi * d**2 / 4.0 * length for d, length in cylinders)
    return volume * P["steel_density_kg_mm3"]


def mass_results() -> dict:
    # CAD-linked preliminary masses for newly defined R05 mechanisms.
    locator_each = volume_mass(
        boxes=[
            (30, 20, 430), (30, 20, 430),  # fixed guide rails
            (160, 180, 12),                 # moving carriage
            (80, 40, 265),                  # conservative solid envelope for RHS mast
            (260, 160, 12),                 # support/mount plate
            (80, 12, 120), (80, 12, 120),   # guide end plates
        ],
        cylinders=[(50, 60), (24, 430), (20, 100), (16, 80), (16, 80)],
    )
    # Correct RHS mast by subtracting its inner void.
    locator_each -= (68 * 28 * 265) * P["steel_density_kg_mm3"]
    retention_each = volume_mass(
        boxes=[(280, 160, 12), (80, 10, 85), (20, 80, 30), (60, 8, 85), (60, 8, 85)],
        cylinders=[(12, 55)] * 4,
    )
    chs_area, _, _ = circular_hollow_properties(42.4, 3.2)
    handle_tube_mass = chs_area * (900 + 2 * 250 + 2 * 100) * P["steel_density_kg_mm3"]
    handle_mass = handle_tube_mass + volume_mass(boxes=[(100, 12, 125), (100, 12, 125), (80, 8, 100), (80, 8, 100)], cylinders=[(12, 60)] * 8)
    rows = [
        {"component": "Rodamiento", "mass_kg": 3032.0, "x_mm": 0.0, "y_mm": 0.0, "z_mm": 1147.5, "state": "VERIFICADO"},
        {"component": "Bastidor W6x9", "mass_kg": 168.125, "x_mm": 0.0, "y_mm": 0.0, "z_mm": 730.0, "state": "R01_CALCULADO"},
        {"component": "Tres PAD", "mass_kg": 21.457, "x_mm": 0.0, "y_mm": 0.0, "z_mm": 847.5, "state": "R04_CALCULADO"},
        {"component": "Cuatro ruedas SPKVS 200K", "mass_kg": 4 * 14.3, "x_mm": 0.0, "y_mm": 0.0, "z_mm": 390.0, "state": "CATALOGO_2026_09_08"},
        {"component": "Horquillas/adaptadores", "mass_kg": 52.0, "x_mm": 0.0, "y_mm": 0.0, "z_mm": 610.0, "state": "ESTIMACION_CAD_R04"},
        {"component": "Tres cassettes centrado R05", "mass_kg": 3 * locator_each, "x_mm": 0.0, "y_mm": 0.0, "z_mm": 820.0, "state": "CALCULADO_GEOMETRIA_R05"},
        {"component": "Tres topes conectados R05", "mass_kg": 3 * retention_each, "x_mm": 0.0, "y_mm": 0.0, "z_mm": 845.0, "state": "CALCULADO_GEOMETRIA_R05"},
        {"component": "Manillar y conexiones R05", "mass_kg": handle_mass, "x_mm": 0.0, "y_mm": -1015.0, "z_mm": 910.0, "state": "CALCULADO_GEOMETRIA_R05"},
        {"component": "Bloqueo central", "mass_kg": 8.0, "x_mm": 0.0, "y_mm": -850.0, "z_mm": 575.0, "state": "HIPOTESIS_R04"},
        {"component": "Tornilleria/guardas/servicios", "mass_kg": 20.0, "x_mm": 0.0, "y_mm": 0.0, "z_mm": 720.0, "state": "RESERVA"},
    ]
    total = sum(r["mass_kg"] for r in rows)
    cg = {
        axis: sum(r["mass_kg"] * r[f"{axis}_mm"] for r in rows) / total
        for axis in ("x", "y", "z")
    }
    return {
        "rows": rows,
        "locator_each_kg": locator_each,
        "retention_each_kg": retention_each,
        "handle_kg": handle_mass,
        "total_kg": total,
        "design_scenario_kg": P["design_mobile_mass_kg"],
        "margin_kg": P["design_mobile_mass_kg"] - total,
        "cg_mm": cg,
        "status": "MASS_WITHIN_3500_SCENARIO" if total <= P["design_mobile_mass_kg"] else "MASS_EXCEEDS_SCENARIO",
    }


def write_csvs(data: dict) -> None:
    with (WORK / "PAD_COVERAGE_R05.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["case", "dx_mm", "dy_mm", "PAD_01", "PAD_02", "PAD_03", "all_full_contact", "design_case"])
        for c in data["pad"]["coverage_cases"]:
            w.writerow([c["case"], c["dx_mm"], c["dy_mm"], *c["coverage_fraction"], c["all_full_contact"], c["design"]])
    with (WORK / "WHEEL_CASES_R05.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["case", "contacts", "missing", "ex_mm", "ey_mm", "W01_kN", "W02_kN", "W03_kN", "W04_kN", "eligible"])
        for c in data["wheel_cases"]:
            w.writerow([c["case"], c["contacts"], c["missing"], c["ex_mm"], c["ey_mm"], *c["reactions_kN"], c["eligible"]])
    with (WORK / "RAIL_ENVELOPE_R05.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["support", "y_mm", "adjacent_max_kN", "continuous_max_kN", "continuous_min_kN"])
        rail = data["rail"]
        for i, y in enumerate(rail["support_positions_mm"]):
            w.writerow([i + 1, y, rail["adjacent_max_by_support_kN"][i], rail["continuous_max_by_support_kN"][i], rail["continuous_min_by_support_kN"][i]])
    with (WORK / "MASS_R05.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["component", "mass_kg", "x_mm", "y_mm", "z_mm", "state"])
        w.writeheader()
        w.writerows(data["mass"]["rows"])


def main() -> None:
    wc = wheel_cases()
    eligible = [c for c in wc if c["eligible"]]
    max_wheel = max(max(c["reactions_kN"]) for c in eligible)
    governing_wheel = max(eligible, key=lambda c: max(c["reactions_kN"]))
    data = {
        "revision": "V5.2_N3_R05_CIERRE_HALLAZGOS_R04",
        "classification": "CORRECCION_MECANICA_SIN_NUEVA_CORRIDA_SAP",
        "warning": "NO LIBERADO PARA FABRICACION; SAP R05 NO EJECUTADO",
        "parameters": P,
        "wheel_cases": wc,
        "wheel": {
            "eligible_cases": len(eligible),
            "governing_case": governing_wheel["case"],
            "max_unfactored_kN": max_wheel,
            "service_selection_kN": max_wheel * P["vertical_service_factor"],
            "uls_local_kN": max_wheel * P["uls_factor"],
            "catalog_dynamic_kN": P["wheel_catalog_dynamic_kg"] * P["g"] / 1000.0,
            "catalog_service_utilization": max_wheel * P["vertical_service_factor"] / (P["wheel_catalog_dynamic_kg"] * P["g"] / 1000.0),
        },
        "pad": pad_results(),
        "mechanisms": mechanism_results(),
        "mass": mass_results(),
    }
    data["rail"] = rail_envelope(wc)
    sensitivity_keys = (
        "support_count",
        "support_pitch_mm",
        "governing_vertical_installation_kN",
        "governing_uplift_continuous_kN",
        "lateral_installation_kN",
        "simple_span_head_stress_MPa",
        "simple_span_base_stress_MPa",
        "simple_span_service_deflection_mm",
    )
    data["rail"]["support_count_sensitivity"] = [
        {key: rail_case[key] for key in sensitivity_keys}
        for rail_case in (rail_envelope(wc, count) for count in (11, 12, 13))
    ]
    write_csvs(data)
    (WORK / "R05_CALC_DATA.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "wheel": data["wheel"],
        "pad": {k: v for k, v in data["pad"].items() if k not in {"coverage_cases", "reaction_cases"}},
        "rail": {k: v for k, v in data["rail"].items() if "by_support" not in k and "positions" not in k},
        "mechanisms": data["mechanisms"],
        "mass": {k: v for k, v in data["mass"].items() if k != "rows"},
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
