"""
ORMÁN-Ops Agent Tools (v2)
6 tools for autonomous wildfire operations agent.
Tools: fetch_fires, check_weather, assess_regional_risk, analyze_threat, plan_response, generate_report
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Kazakhstan regions including fire-prone forest areas
KZ_REGIONS = {
    # === Fire-Prone Forest Areas (Priority) ===
    "Semey Ormanı": {
        "lat": 50.2, "lon": 80.3,
        "area": "Семей орманы — World's largest relict pine forest",
        "vegetation": "pine_forest", "elevation_m": 350,
        "historical_fires_yearly": 85,
        "fire_season": "April-September",
        "description_ru": "Реликтовый сосновый бор — один из крупнейших в мире"
    },
    "Burabay": {
        "lat": 53.08, "lon": 70.3,
        "area": "Бурабай — National Park, dense mixed forest",
        "vegetation": "mixed_forest", "elevation_m": 450,
        "historical_fires_yearly": 25,
        "fire_season": "May-August",
        "description_ru": "Национальный парк Бурабай — густой смешанный лес"
    },
    "Bayanaul": {
        "lat": 50.8, "lon": 75.7,
        "area": "Баянаул — Mountain forest national park",
        "vegetation": "mountain_forest", "elevation_m": 680,
        "historical_fires_yearly": 20,
        "fire_season": "May-August",
        "description_ru": "Баянаульский национальный парк — горный лес"
    },
    "Karkaraly": {
        "lat": 49.4, "lon": 75.5,
        "area": "Каркаралы — Forest-steppe mountain area",
        "vegetation": "forest_steppe", "elevation_m": 900,
        "historical_fires_yearly": 18,
        "fire_season": "May-September",
        "description_ru": "Каркаралинский национальный парк"
    },
    # === Major Regions ===
    "Almaty Region": {
        "lat": 44.0, "lon": 77.0,
        "area": "Алматинская область",
        "vegetation": "mixed_forest", "elevation_m": 600,
        "historical_fires_yearly": 35,
        "fire_season": "May-September",
        "description_ru": "Алматинская область — горные леса Тянь-Шаня"
    },
    "East Kazakhstan": {
        "lat": 49.9, "lon": 82.6,
        "area": "Восточно-Казахстанская область",
        "vegetation": "taiga_forest", "elevation_m": 700,
        "historical_fires_yearly": 60,
        "fire_season": "April-September",
        "description_ru": "ВКО — таёжные леса Алтая"
    },
    "Kostanay": {
        "lat": 53.2, "lon": 63.6,
        "area": "Костанайская область",
        "vegetation": "steppe_grassland", "elevation_m": 180,
        "historical_fires_yearly": 40,
        "fire_season": "May-August",
        "description_ru": "Костанайская область — степные пожары"
    },
    "Karaganda": {
        "lat": 49.8, "lon": 73.1,
        "area": "Карагандинская область",
        "vegetation": "steppe", "elevation_m": 550,
        "historical_fires_yearly": 30,
        "fire_season": "May-August",
        "description_ru": "Карагандинская область"
    },
    "Akmola": {
        "lat": 51.5, "lon": 69.0,
        "area": "Акмолинская область",
        "vegetation": "steppe_forest", "elevation_m": 380,
        "historical_fires_yearly": 22,
        "fire_season": "May-August",
        "description_ru": "Акмолинская область"
    },
    "Pavlodar": {
        "lat": 52.3, "lon": 76.9,
        "area": "Павлодарская область",
        "vegetation": "steppe", "elevation_m": 120,
        "historical_fires_yearly": 28,
        "fire_season": "May-August",
        "description_ru": "Павлодарская область"
    },
    "Turkestan": {
        "lat": 43.3, "lon": 68.25,
        "area": "Туркестанская область",
        "vegetation": "semi_arid", "elevation_m": 500,
        "historical_fires_yearly": 15,
        "fire_season": "June-September",
        "description_ru": "Туркестанская область"
    },
    "Abai": {
        "lat": 47.8, "lon": 80.2,
        "area": "Область Абай",
        "vegetation": "steppe_forest", "elevation_m": 450,
        "historical_fires_yearly": 35,
        "fire_season": "April-September",
        "description_ru": "Область Абай"
    },
    "Zhetysu": {
        "lat": 45.0, "lon": 79.0,
        "area": "Область Жетысу",
        "vegetation": "mixed_forest", "elevation_m": 550,
        "historical_fires_yearly": 20,
        "fire_season": "May-September",
        "description_ru": "Область Жетысу"
    },
    "North Kazakhstan": {
        "lat": 54.9, "lon": 69.1,
        "area": "Северо-Казахстанская область",
        "vegetation": "forest_steppe", "elevation_m": 130,
        "historical_fires_yearly": 15,
        "fire_season": "May-August",
        "description_ru": "СКО"
    },
    "West Kazakhstan": {
        "lat": 51.2, "lon": 51.4,
        "area": "Западно-Казахстанская область",
        "vegetation": "semi_arid", "elevation_m": 50,
        "historical_fires_yearly": 12,
        "fire_season": "June-August",
        "description_ru": "ЗКО"
    },
    "Mangystau": {
        "lat": 43.3, "lon": 52.1,
        "area": "Мангистауская область",
        "vegetation": "desert", "elevation_m": 50,
        "historical_fires_yearly": 5,
        "fire_season": "June-August",
        "description_ru": "Мангистауская область"
    },
}

# Vegetation fire risk multipliers
VEGETATION_RISK = {
    "pine_forest": 1.0,
    "taiga_forest": 0.95,
    "mixed_forest": 0.8,
    "mountain_forest": 0.7,
    "forest_steppe": 0.65,
    "steppe_forest": 0.6,
    "steppe_grassland": 0.55,
    "steppe": 0.5,
    "semi_arid": 0.35,
    "desert": 0.15,
}


# ──────────────────────────────────────────────
# TOOL 1: Fetch Fire Data from NASA FIRMS
# ──────────────────────────────────────────────
def fetch_fires(region: str, firms_api_key: str, days_back: int = 10) -> Dict[str, Any]:
    """Fetch live wildfire data from NASA FIRMS API (VIIRS SNPP)."""
    region_data = KZ_REGIONS.get(region)
    if not region_data:
        return {"status": "error", "message": f"Region '{region}' not found.", "data": []}
    
    lat, lon = region_data["lat"], region_data["lon"]
    delta = 2.5  # ~250km radius
    west, east = lon - delta, lon + delta
    south, north = lat - delta, lat + delta
    
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{firms_api_key}/VIIRS_SNPP_NRT/{west},{south},{east},{north}/{days_back}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            if len(lines) <= 1:
                return {
                    "status": "success",
                    "region": region,
                    "coords": {"lat": lat, "lon": lon},
                    "fire_count": 0,
                    "data": [],
                    "total_detections": 0,
                    "period": f"Last {days_back} days",
                    "source": "VIIRS SNPP (NASA FIRMS)",
                    "message": f"No active fires detected in {region} in the last {days_back} days."
                }
            
            headers = lines[0].split(',')
            fires = []
            for line in lines[1:]:
                values = line.split(',')
                if len(values) >= len(headers):
                    fires.append(dict(zip(headers, values)))
            
            return {
                "status": "success",
                "region": region,
                "coords": {"lat": lat, "lon": lon},
                "fire_count": len(fires),
                "data": fires[:50],
                "total_detections": len(fires),
                "period": f"Last {days_back} days",
                "source": "VIIRS SNPP (NASA FIRMS)"
            }
        else:
            return {
                "status": "error",
                "message": f"FIRMS API error: status {response.status_code}",
                "region": region,
                "coords": {"lat": lat, "lon": lon},
                "data": []
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"FIRMS request failed: {str(e)}",
            "region": region,
            "coords": {"lat": lat, "lon": lon},
            "data": []
        }


# ──────────────────────────────────────────────
# TOOL 2: Check Weather Conditions (Open-Meteo)
# ──────────────────────────────────────────────
def check_weather(region: str) -> Dict[str, Any]:
    """Fetch current weather from Open-Meteo API. No API key needed."""
    region_data = KZ_REGIONS.get(region)
    if not region_data:
        return {"status": "error", "message": f"Region '{region}' not found."}
    
    lat, lon = region_data["lat"], region_data["lon"]
    
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,"
        f"wind_direction_10m,wind_gusts_10m,precipitation"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        f"wind_speed_10m_max,relative_humidity_2m_min"
        f"&timezone=Asia/Almaty&forecast_days=3"
    )
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            daily = data.get("daily", {})
            
            temp = current.get("temperature_2m", 0)
            humidity = current.get("relative_humidity_2m", 0)
            wind_speed = current.get("wind_speed_10m", 0)
            wind_dir = current.get("wind_direction_10m", 0)
            wind_gusts = current.get("wind_gusts_10m", 0)
            precip = current.get("precipitation", 0)
            
            # Fire Weather Index (simplified)
            fire_weather_risk = "LOW"
            fwi_score = 0
            
            # Temperature factor
            if temp > 35: fwi_score += 30
            elif temp > 30: fwi_score += 22
            elif temp > 25: fwi_score += 15
            elif temp > 20: fwi_score += 8
            
            # Humidity factor (low humidity = high risk)
            if humidity < 20: fwi_score += 30
            elif humidity < 30: fwi_score += 22
            elif humidity < 40: fwi_score += 15
            elif humidity < 50: fwi_score += 8
            
            # Wind factor
            if wind_speed > 40: fwi_score += 25
            elif wind_speed > 25: fwi_score += 18
            elif wind_speed > 15: fwi_score += 10
            elif wind_speed > 8: fwi_score += 5
            
            # Precipitation factor (recent rain reduces risk)
            if precip > 5: fwi_score -= 15
            elif precip > 1: fwi_score -= 8
            
            fwi_score = max(0, min(100, fwi_score))
            
            if fwi_score >= 65: fire_weather_risk = "EXTREME"
            elif fwi_score >= 50: fire_weather_risk = "HIGH"
            elif fwi_score >= 35: fire_weather_risk = "MODERATE"
            elif fwi_score >= 15: fire_weather_risk = "LOW"
            else: fire_weather_risk = "MINIMAL"
            
            # Wind direction as compass
            directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                          "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            wind_compass = directions[int((wind_dir + 11.25) / 22.5) % 16]
            
            return {
                "status": "success",
                "region": region,
                "current": {
                    "temperature_c": temp,
                    "humidity_pct": humidity,
                    "wind_speed_kmh": wind_speed,
                    "wind_gusts_kmh": wind_gusts,
                    "wind_direction_deg": wind_dir,
                    "wind_direction_compass": wind_compass,
                    "precipitation_mm": precip,
                },
                "forecast_3day": {
                    "dates": daily.get("time", []),
                    "max_temps": daily.get("temperature_2m_max", []),
                    "min_temps": daily.get("temperature_2m_min", []),
                    "precip_sum": daily.get("precipitation_sum", []),
                    "max_wind": daily.get("wind_speed_10m_max", []),
                    "min_humidity": daily.get("relative_humidity_2m_min", []),
                },
                "fire_weather_index": {
                    "score": fwi_score,
                    "risk_level": fire_weather_risk,
                },
                "analysis": (
                    f"Temperature: {temp}°C, Humidity: {humidity}%, "
                    f"Wind: {wind_speed} km/h ({wind_compass}), Gusts: {wind_gusts} km/h, "
                    f"Precipitation: {precip}mm. "
                    f"Fire Weather Risk: {fire_weather_risk} (score: {fwi_score}/100)."
                )
            }
        else:
            return {"status": "error", "message": f"Open-Meteo error: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"Weather request failed: {str(e)}"}


# ──────────────────────────────────────────────
# TOOL 3: Assess Regional Fire Risk
# ──────────────────────────────────────────────
def assess_regional_risk(region: str) -> Dict[str, Any]:
    """Assess historical and environmental fire risk for a region."""
    region_data = KZ_REGIONS.get(region)
    if not region_data:
        return {"status": "error", "message": f"Region '{region}' not found."}
    
    vegetation = region_data.get("vegetation", "steppe")
    veg_risk = VEGETATION_RISK.get(vegetation, 0.5)
    historical_fires = region_data.get("historical_fires_yearly", 20)
    fire_season = region_data.get("fire_season", "May-August")
    elevation = region_data.get("elevation_m", 300)
    
    # Current month check
    now = datetime.now()
    month = now.month
    month_name = now.strftime("%B")
    
    # Parse fire season
    season_months = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }
    season_parts = fire_season.split("-")
    if len(season_parts) == 2:
        start_month = season_months.get(season_parts[0], 5)
        end_month = season_months.get(season_parts[1], 8)
        in_fire_season = start_month <= month <= end_month
    else:
        in_fire_season = 5 <= month <= 8
    
    # Seasonal risk multiplier
    if in_fire_season:
        season_risk = 0.9
        season_status = f"ACTIVE — Currently in fire season ({fire_season})"
    elif abs(month - 5) <= 1 or abs(month - 8) <= 1:
        season_risk = 0.5
        season_status = f"APPROACHING — Near fire season ({fire_season})"
    else:
        season_risk = 0.2
        season_status = f"OFF-SEASON — Fire season is {fire_season}"
    
    # Composite risk score (0-100)
    risk_score = (
        veg_risk * 35 +                           # Vegetation: 0-35
        min(35, historical_fires / 85 * 35) +       # Historical: 0-35
        season_risk * 30                             # Seasonal: 0-30
    )
    risk_score = round(min(100, risk_score), 1)
    
    if risk_score >= 70: risk_level = "VERY HIGH"
    elif risk_score >= 55: risk_level = "HIGH"
    elif risk_score >= 40: risk_level = "MODERATE"
    elif risk_score >= 20: risk_level = "LOW"
    else: risk_level = "MINIMAL"
    
    return {
        "status": "success",
        "region": region,
        "risk_assessment": {
            "overall_risk_score": risk_score,
            "risk_level": risk_level,
            "vegetation_type": vegetation,
            "vegetation_risk_factor": round(veg_risk, 2),
            "historical_fires_per_year": historical_fires,
            "fire_season": fire_season,
            "season_status": season_status,
            "in_fire_season": in_fire_season,
            "elevation_m": elevation,
            "current_month": month_name,
        },
        "description_ru": region_data.get("description_ru", ""),
        "analysis": (
            f"Region: {region} | Risk Level: {risk_level} (score: {risk_score}/100). "
            f"Vegetation: {vegetation} (risk factor: {veg_risk:.2f}). "
            f"Historical average: {historical_fires} fires/year. "
            f"Season: {season_status}."
        )
    }


# ──────────────────────────────────────────────
# TOOL 4: Analyze Threat Level
# ──────────────────────────────────────────────
def analyze_threat(
    firms_result: Dict[str, Any],
    weather_result: Dict[str, Any] = None,
    risk_result: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Comprehensive threat analysis combining fire data, weather, and regional risk."""
    
    fire_count = firms_result.get("fire_count", 0)
    fires = firms_result.get("data", [])
    region = firms_result.get("region", "Unknown")
    
    # === Fire metrics ===
    frp_values, brightness_values, positions = [], [], []
    high_conf_count = 0
    
    for fire in fires:
        try: frp_values.append(float(fire.get("frp", 0)))
        except: frp_values.append(0)
        try: brightness_values.append(float(fire.get("bright_ti4", fire.get("brightness", 0))))
        except: brightness_values.append(0)
        conf = fire.get("confidence", "").lower()
        if conf in ["high", "h"] or (conf.isdigit() and int(conf) > 80):
            high_conf_count += 1
        try: positions.append({"lat": float(fire.get("latitude", 0)), "lon": float(fire.get("longitude", 0))})
        except: pass
    
    avg_frp = sum(frp_values) / len(frp_values) if frp_values else 0
    max_frp = max(frp_values) if frp_values else 0
    avg_brightness = sum(brightness_values) / len(brightness_values) if brightness_values else 0
    clusters = _count_clusters([(p["lat"], p["lon"]) for p in positions])
    
    # === Scoring (0-100) ===
    score = 0
    confidence_factors = []
    
    # Fire component (0-30)
    fire_score = min(30, fire_count * 3)
    score += fire_score
    confidence_factors.append(f"Fire detections: {fire_count} (+{fire_score:.0f})")
    
    # FRP component (0-20)
    if avg_frp > 50: frp_score = 20
    elif avg_frp > 20: frp_score = 14
    elif avg_frp > 10: frp_score = 8
    elif avg_frp > 0: frp_score = 4
    else: frp_score = 0
    score += frp_score
    confidence_factors.append(f"Avg FRP: {avg_frp:.1f} MW (+{frp_score})")
    
    # Weather component (0-25)
    weather_score = 0
    if weather_result and weather_result.get("status") == "success":
        fwi = weather_result.get("fire_weather_index", {})
        fwi_score = fwi.get("score", 0)
        weather_score = min(25, fwi_score * 0.25)
        wind = weather_result.get("current", {}).get("wind_speed_kmh", 0)
        confidence_factors.append(
            f"Fire Weather Index: {fwi_score}/100, Wind: {wind} km/h (+{weather_score:.0f})"
        )
    score += weather_score
    
    # Regional risk component (0-25)
    regional_score = 0
    if risk_result and risk_result.get("status") == "success":
        risk_data = risk_result.get("risk_assessment", {})
        regional_risk = risk_data.get("overall_risk_score", 0)
        regional_score = min(25, regional_risk * 0.25)
        confidence_factors.append(
            f"Regional risk: {regional_risk}/100 ({risk_data.get('risk_level', 'N/A')}) (+{regional_score:.0f})"
        )
    score += regional_score
    
    score = round(min(100, score), 1)
    
    # Confidence percentage (how sure the agent is about the assessment)
    data_sources = 1  # FIRMS always present
    if weather_result and weather_result.get("status") == "success": data_sources += 1
    if risk_result and risk_result.get("status") == "success": data_sources += 1
    confidence_pct = round(min(98, 40 + data_sources * 15 + (fire_count > 0) * 13), 1)
    
    # Threat level
    if score >= 70: threat_level = "CRITICAL"
    elif score >= 50: threat_level = "HIGH"
    elif score >= 30: threat_level = "MODERATE"
    elif score >= 10: threat_level = "LOW"
    else: threat_level = "MINIMAL"
    
    # Determine scenario
    if fire_count > 0:
        scenario = "ACTIVE_FIRE"
        scenario_desc = f"{fire_count} active fire(s) detected — emergency assessment mode"
    else:
        scenario = "PREVENTIVE"
        scenario_desc = "No active fires — preventive risk assessment mode"
    
    return {
        "status": "success",
        "region": region,
        "scenario": scenario,
        "scenario_description": scenario_desc,
        "threat_level": threat_level,
        "threat_score": score,
        "confidence_pct": confidence_pct,
        "confidence_factors": confidence_factors,
        "fire_metrics": {
            "fire_count": fire_count,
            "avg_frp_mw": round(avg_frp, 2),
            "max_frp_mw": round(max_frp, 2),
            "avg_brightness_k": round(avg_brightness, 2),
            "high_confidence_count": high_conf_count,
            "clusters": clusters,
        },
        "fire_locations": positions[:30],
        "analysis": (
            f"Threat Level: {threat_level} (score: {score}/100, confidence: {confidence_pct}%). "
            f"Scenario: {scenario_desc}. "
            f"Scoring breakdown: {'; '.join(confidence_factors)}."
        )
    }


# ──────────────────────────────────────────────
# TOOL 5: Plan Response
# ──────────────────────────────────────────────
def plan_response(
    threat_analysis: Dict[str, Any],
    weather_result: Dict[str, Any] = None,
    region: str = ""
) -> Dict[str, Any]:
    """Generate emergency or preventive response plan based on threat analysis."""
    
    threat_level = threat_analysis.get("threat_level", "LOW")
    scenario = threat_analysis.get("scenario", "PREVENTIVE")
    details = threat_analysis.get("fire_metrics", {})
    fire_count = details.get("fire_count", 0)
    clusters = details.get("clusters", 0)
    
    # Wind data for spread prediction
    wind_speed = 0
    wind_dir = ""
    if weather_result and weather_result.get("status") == "success":
        current = weather_result.get("current", {})
        wind_speed = current.get("wind_speed_kmh", 0)
        wind_dir = current.get("wind_direction_compass", "N")
    
    if scenario == "ACTIVE_FIRE":
        # === EMERGENCY RESPONSE ===
        resource_plans = {
            "CRITICAL": {
                "fire_brigades": max(5, clusters * 3),
                "helicopters": max(2, clusters),
                "evacuation_buses": max(10, fire_count * 2),
                "medical_teams": max(3, clusters * 2),
                "water_tankers": max(4, clusters * 2),
                "evacuation_radius_km": 15 + (5 if wind_speed > 30 else 0),
                "alert_level": "КРАСНЫЙ — Немедленная эвакуация / RED — Immediate Evacuation",
            },
            "HIGH": {
                "fire_brigades": max(3, clusters * 2),
                "helicopters": max(1, clusters),
                "evacuation_buses": max(5, fire_count),
                "medical_teams": max(2, clusters),
                "water_tankers": max(3, clusters),
                "evacuation_radius_km": 10 + (3 if wind_speed > 25 else 0),
                "alert_level": "ОРАНЖЕВЫЙ — Готовность к эвакуации / ORANGE — Prepare Evacuation",
            },
            "MODERATE": {
                "fire_brigades": max(2, clusters),
                "helicopters": 0,
                "evacuation_buses": 2,
                "medical_teams": 1,
                "water_tankers": max(2, clusters),
                "evacuation_radius_km": 5,
                "alert_level": "ЖЁЛТЫЙ — Усиленный мониторинг / YELLOW — Enhanced Monitoring",
            },
        }
        plan = resource_plans.get(threat_level, resource_plans.get("MODERATE"))
        
        actions = []
        if threat_level == "CRITICAL":
            actions = [
                "НЕМЕДЛЕННО: Активировать систему экстренного оповещения",
                "НЕМЕДЛЕННО: Развернуть все пожарные бригады к очагам",
                f"В ТЕЧЕНИЕ 15 МИН: Начать эвакуацию в радиусе {plan['evacuation_radius_km']} км",
                f"ВНИМАНИЕ: Ветер {wind_speed} км/ч ({wind_dir}) — огонь может распространяться в направлении {_opposite_direction(wind_dir)}",
                "В ТЕЧЕНИЕ 30 МИН: Запросить авиационную поддержку",
                "В ТЕЧЕНИЕ 1 ЧАСА: Развернуть эвакуационные пункты",
                "ПОСТОЯННО: Координация с ДЧС МВД РК",
            ]
        elif threat_level == "HIGH":
            actions = [
                "НЕМЕДЛЕННО: Оповестить пожарные части и резервные подразделения",
                "В ТЕЧЕНИЕ 30 МИН: Направить бригады к очагам возгорания",
                f"ВНИМАНИЕ: Ветер {wind_speed} км/ч ({wind_dir}) — контролировать распространение",
                "В ТЕЧЕНИЕ 1 ЧАСА: Объявить предупреждение об эвакуации",
                "В ТЕЧЕНИЕ 2 ЧАСОВ: Подготовить эвакуационные пункты",
                "ПОСТОЯННО: Мониторинг спутниковых данных каждые 30 минут",
            ]
        else:
            actions = [
                "Привести местные пожарные станции в состояние готовности",
                "Направить наземную разведку к координатам возгорания",
                "Выпустить предупреждение для населения",
                f"Учитывать направление ветра: {wind_speed} км/ч ({wind_dir})",
                "Мониторинг спутниковых данных каждые 2 часа",
            ]
        
        plan_type = "EMERGENCY"
    else:
        # === PREVENTIVE PLAN ===
        plan = {
            "fire_brigades": 1,
            "helicopters": 0,
            "evacuation_buses": 0,
            "medical_teams": 0,
            "water_tankers": 1,
            "evacuation_radius_km": 0,
            "alert_level": "ЗЕЛЁНЫЙ — Превентивная готовность / GREEN — Preventive Readiness",
        }
        
        risk_level = threat_analysis.get("threat_level", "LOW")
        actions = [
            f"Текущая оценка: Активных пожаров нет. Уровень риска: {risk_level}",
            "Обеспечить готовность пожарных подразделений в регионе",
            f"Метеоусловия: ветер {wind_speed} км/ч ({wind_dir})",
        ]
        
        if risk_level in ["HIGH", "CRITICAL"]:
            actions.extend([
                "РЕКОМЕНДАЦИЯ: Усилить патрулирование лесных массивов",
                "Предварительно разместить водовозы в зонах повышенного риска",
                "Подготовить план эвакуации для ближайших населённых пунктов",
                "Установить дополнительные камеры наблюдения в лесных зонах",
            ])
        elif risk_level == "MODERATE":
            actions.extend([
                "Проводить регулярное патрулирование",
                "Проверить исправность противопожарного оборудования",
                "Обновить планы эвакуации для населённых пунктов",
            ])
        else:
            actions.extend([
                "Продолжать стандартный мониторинг",
                "Проверить готовность оборудования к пожароопасному сезону",
            ])
        
        plan_type = "PREVENTIVE"
    
    return {
        "status": "success",
        "region": region,
        "plan_type": plan_type,
        "alert_level": plan["alert_level"],
        "resources": plan,
        "priority_actions": actions,
        "wind_info": {
            "speed_kmh": wind_speed,
            "direction": wind_dir,
            "spread_risk_direction": _opposite_direction(wind_dir),
        },
        "coordination": {
            "primary": "Региональный ДЧС (Департамент по чрезвычайным ситуациям)",
            "secondary": "Местный акимат (администрация)",
            "national": "МЧС Республики Казахстан",
        },
        "timestamp": datetime.now().isoformat(),
    }


# ──────────────────────────────────────────────
# TOOL 6: Generate Final Report
# ──────────────────────────────────────────────
def generate_report(
    region: str,
    firms_result: Dict[str, Any],
    weather_result: Dict[str, Any],
    risk_result: Dict[str, Any],
    threat_analysis: Dict[str, Any],
    response_plan: Dict[str, Any]
) -> Dict[str, Any]:
    """Compile all data into a structured operational report."""
    
    return {
        "title": f"ORMÁN-Ops — Оперативный отчёт: {region}",
        "title_en": f"ORMÁN-Ops — Operational Report: {region}",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S (UTC+6)"),
        "executive_summary": {
            "region": region,
            "region_description": KZ_REGIONS.get(region, {}).get("description_ru", ""),
            "scenario": threat_analysis.get("scenario", "UNKNOWN"),
            "scenario_description": threat_analysis.get("scenario_description", ""),
            "threat_level": threat_analysis.get("threat_level", "UNKNOWN"),
            "threat_score": threat_analysis.get("threat_score", 0),
            "confidence_pct": threat_analysis.get("confidence_pct", 0),
            "fires_detected": firms_result.get("fire_count", 0),
            "data_source": firms_result.get("source", "VIIRS SNPP (NASA FIRMS)"),
            "monitoring_period": firms_result.get("period", "N/A"),
            "alert_level": response_plan.get("alert_level", "N/A"),
            "plan_type": response_plan.get("plan_type", "N/A"),
        },
        "satellite_data": {
            "total_detections": firms_result.get("total_detections", 0),
            "fire_metrics": threat_analysis.get("fire_metrics", {}),
        },
        "weather_conditions": weather_result.get("current", {}) if weather_result else {},
        "fire_weather_index": weather_result.get("fire_weather_index", {}) if weather_result else {},
        "forecast_3day": weather_result.get("forecast_3day", {}) if weather_result else {},
        "regional_risk": risk_result.get("risk_assessment", {}) if risk_result else {},
        "threat_assessment": {
            "level": threat_analysis.get("threat_level", "UNKNOWN"),
            "score": threat_analysis.get("threat_score", 0),
            "confidence": threat_analysis.get("confidence_pct", 0),
            "scoring_breakdown": threat_analysis.get("confidence_factors", []),
        },
        "response_plan": {
            "type": response_plan.get("plan_type", "N/A"),
            "alert_level": response_plan.get("alert_level", ""),
            "resources": response_plan.get("resources", {}),
            "priority_actions": response_plan.get("priority_actions", []),
            "wind_info": response_plan.get("wind_info", {}),
            "coordination": response_plan.get("coordination", {}),
        },
        "fire_locations": threat_analysis.get("fire_locations", []),
        "data_sources_used": [
            "NASA FIRMS VIIRS SNPP (спутниковые данные о пожарах)",
            "Open-Meteo (метеорологические данные)",
            "Regional risk database (исторические данные о пожарах)",
        ],
    }


# ──────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────
def _count_clusters(positions: List[tuple], threshold: float = 0.1) -> int:
    if not positions: return 0
    visited = set()
    clusters = 0
    for i, (lat1, lon1) in enumerate(positions):
        if i in visited: continue
        clusters += 1
        visited.add(i)
        for j, (lat2, lon2) in enumerate(positions):
            if j not in visited:
                if ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5 < threshold:
                    visited.add(j)
    return clusters


def _opposite_direction(direction: str) -> str:
    opposites = {
        "N": "S", "S": "N", "E": "W", "W": "E",
        "NE": "SW", "NW": "SE", "SE": "NW", "SW": "NE",
        "NNE": "SSW", "ENE": "WSW", "ESE": "WNW", "SSE": "NNW",
        "SSW": "NNE", "WSW": "ENE", "WNW": "ESE", "NNW": "SSE",
    }
    return opposites.get(direction, "unknown")
