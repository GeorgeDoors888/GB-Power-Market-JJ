import json
from pathlib import Path
import pandas as pd
import folium
from folium import GeoJson
from folium.plugins import MarkerCluster, TimestampedGeoJson, HeatMap

MAP_OUT = "out/map.html"

def _parse_geojson(df, key_geo="geojson"):
    out = []
    for _, row in df.iterrows():
        gj = row[key_geo]
        try:
            geo = json.loads(gj)
        except Exception:
            continue
        props = row.to_dict()
        props.pop(key_geo, None)
        out.append((props, geo))
    return out

def _color_scale_prob(val):
    low, mid, high = ("#88CCEE", "#F5A623", "#FF0000")
    if val is None:
        return "#CCCCCC"
    if val < 0.15:
        return low
    if val < 0.40:
        return mid
    return high

def _color_scale_headroom(h):
    high, med, low = ("#22C55E", "#FACC15", "#EF4444")
    if h is None:
        return "#6B7280"
    if h > 0.3:
        return high
    if h > 0.1:
        return med
    return low

def build_dynamic_map(
    gsp_geo,
    dno_geo,
    wind_geo,
    ic_geo,
    constraints_df,
    gsp_headroom_df,
    wind_df,
    turbine_df,
    ic_flows_df,
    filters,
    html_out=MAP_OUT,
):
    m = folium.Map(location=[54.5, -2.5], zoom_start=6, tiles="CartoDB dark_matter")
    folium.TileLayer("CartoDB positron").add_to(m)

    # DNO outlines (light)
    if not dno_geo.empty:
        for props, geo in _parse_geojson(dno_geo):
            GeoJson(
                geo,
                name=f"DNO {props.get('dno')}",
                style_function=lambda x: {
                    "fillColor": "#00000000",
                    "color": "#FFFFFF33",
                    "weight": 1,
                },
            ).add_to(m)

    # GSP polygons with combined constraint prob + headroom (Phase 11)
    cons_map = {}
    if constraints_df is not None and not constraints_df.empty and "gsp" in constraints_df.columns:
        cons_map = {
            row["gsp"]: row.get("constraint_prob", None)
            for _, row in constraints_df.iterrows()
        }

    headroom_map = {}
    if gsp_headroom_df is not None and not gsp_headroom_df.empty and "gsp" in gsp_headroom_df.columns:
        latest = gsp_headroom_df.sort_values("timestamp").groupby("gsp").tail(1)
        headroom_map = {
            row["gsp"]: {
                "headroom_mw": row.get("headroom_mw"),
                "headroom_pct": row.get("headroom_pct"),
                "demand_mw": row.get("demand_mw"),
                "gen_mw": row.get("gen_mw"),
            }
            for _, row in latest.iterrows()
        }

    if not gsp_geo.empty:
        for props, geo in _parse_geojson(gsp_geo):
            gsp = props.get("gsp")
            prob = cons_map.get(gsp, None)
            hrow = headroom_map.get(gsp, {})
            h_pct = hrow.get("headroom_pct")
            # Colour primarily by constraint probability, modulated by headroom
            color = _color_scale_prob(prob)
            border_color = _color_scale_headroom(h_pct)
            popup_html = f"""<div style='font-size:12px'>
                <b>GSP:</b> {gsp}<br>
                <b>DNO:</b> {props.get('dno')}<br>
                <b>Constraint probability:</b> {prob if prob is not None else 'N/A'}<br>
                <b>Headroom:</b> {hrow.get('headroom_mw','?')} MW ({(h_pct*100):.1f}% if h_pct not in [None] else 'N/A')<br>
                <b>Demand:</b> {hrow.get('demand_mw','?')} MW<br>
                <b>Generation:</b> {hrow.get('gen_mw','?')} MW<br>
            </div>"""  # noqa: E501
            GeoJson(
                geo,
                name=f"GSP {gsp}",
                style_function=lambda x, c=color, bc=border_color: {
                    "fillColor": c,
                    "color": bc,
                    "weight": 1.5,
                    "fillOpacity": 0.45,
                },
                tooltip=f"GSP {gsp}",
                popup=folium.Popup(popup_html, max_width=320),
            ).add_to(m)

    # Wind farm polygons
    if not wind_geo.empty:
        for props, geo in _parse_geojson(wind_geo):
            farm = props.get("farm_name")
            cap = props.get("capacity_mw")
            popup_html = f"<b>Wind Farm:</b> {farm}<br><b>Capacity:</b> {cap} MW<br>"
            GeoJson(
                geo,
                name=f"Wind Farm {farm}",
                style_function=lambda x: {
                    "fillColor": "#F5A62355",
                    "color": "#F5A623",
                    "weight": 1,
                },
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{farm}",
            ).add_to(m)

    # Turbine markers: error & forecast (Phase 11 turbine ML)
    if not turbine_df.empty:
        cluster = MarkerCluster(name="Turbines").add_to(m)
        for _, row in turbine_df.iterrows():
            lat = row.get("lat")
            lon = row.get("lon")
            if lat is None or lon is None:
                continue
            error = row.get("turbine_error_mw")
            farm = row.get("farm_name")
            tid = row.get("turbine_id")
            f_mw = row.get("forecast_mw")
            f_err = row.get("forecast_err_mw")
            color = "#22CC22"
            if error is not None and error > 2:
                color = "#FF4444"
            popup_html = f"""<b>{farm} - Turbine {tid}</b><br>
                <b>Error:</b> {error} MW<br>
                <b>Forecast:</b> {f_mw} MW<br>
                <b>Forecast error:</b> {f_err} MW<br>
            """
            folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                fill=True,
                color=color,
                fill_opacity=0.8,
                popup=popup_html,
                tooltip=f"{farm}-{tid}",
            ).add_to(cluster)

    # Interconnector polylines + arrows (ESO-style)
    if not ic_geo.empty:
        for props, geo in _parse_geojson(ic_geo):
            name = props.get("name")
            popup_html = f"<b>Interconnector:</b> {name}<br>"
            GeoJson(
                geo,
                name=f"IC {name}",
                style_function=lambda x: {
                    "color": "#006FBD",
                    "weight": 3,
                    "opacity": 0.7,
                },
                popup=folium.Popup(popup_html, max_width=300),
            ).add_to(m)

    # Overlay arrows for latest IC flows (if available)
    if ic_flows_df is not None and not ic_flows_df.empty:
        latest_flows = ic_flows_df.sort_values("timestamp").groupby("ic_name").tail(1)
        for _, row in latest_flows.iterrows():
            flow = row.get("flow_mw", 0.0)
            name = row.get("ic_name")
            # For now we just encode magnitude via line colour & tooltip – the
            # geometry itself comes from geo_interconnectors layer above.
            # More advanced: join to specific coordinates and draw directional segments.
            popup = f"<b>{name}</b><br>Flow: {flow} MW"
            folium.Marker(
                location=[54.5, -2.5],  # fallback central marker; adjust when joining to coords
                icon=folium.DivIcon(html=f"<div style='color:#fff;font-size:10px'>{name}<br>{flow:.0f} MW</div>"),
                popup=popup,
            ).add_to(m)

    # Wind error heatmap
    if filters.get("heatmap", False) and wind_df is not None and not wind_df.empty:
        heat = wind_df[["lat", "lon", "pct_err"]].dropna()
        HeatMap(
            data=heat.values.tolist(),
            name="Wind Error Heatmap",
            min_opacity=0.3,
            radius=18,
            blur=15,
        ).add_to(m)

    # Timeline slider for wind (optional)
    if filters.get("timeline", False) and wind_df is not None and not wind_df.empty:
        wind_df["timestamp"] = pd.to_datetime(wind_df["timestamp"])
        features = []
        for _, row in wind_df.iterrows():
            gj = {
                "type": "Feature",
                "properties": {
                    "time": row["timestamp"].isoformat(),
                    "popup": f"{row['farm_name']}: {row['pct_err']*100:.1f}%",
                    "style": {"color": "#F5A623"},
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [row["lon"], row["lat"]],
                },
            }
            features.append(gj)
        TimestampedGeoJson(
            {"type": "FeatureCollection", "features": features},
            period="PT30M",
            auto_play=True,
            loop=True,
            max_speed=10,
            loop_button=True,
            date_options="YYYY-MM-DD HH:mm",
            time_slider_drag=True,
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    Path(html_out).parent.mkdir(exist_ok=True, parents=True)
    m.save(html_out)
    return html_out
