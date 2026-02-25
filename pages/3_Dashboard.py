import streamlit as st
import pandas as pd
import pydeck as pdk

from utils.io import load_data
from utils.style import inject_css

# ------------------------
# Optional: Snap points to street geometry from OpenStreetMap (OSM)
# ------------------------
import random
import re
import unicodedata

try:
    import osmnx as ox
    from shapely.geometry import LineString, MultiLineString
    from shapely.ops import linemerge

    OSMNX_OK = True
    ox.settings.use_cache = True
    ox.settings.log_console = False
except Exception:
    # If osmnx/geopandas stack isn't installed, app still runs without snapping.
    OSMNX_OK = False


def strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def street_variants(street: str) -> list[str]:
    """
    Generate a few name variants to increase OSM match rate.
    Examples: "Đường Trần Hưng Đạo" -> ["Đường Trần Hưng Đạo", "Trần Hưng Đạo", "Tran Hung Dao"]
    """
    s = str(street or "").strip()
    s2 = re.sub(r"^(đường|duong|đ\.)\s+", "", s, flags=re.IGNORECASE).strip()
    return list(dict.fromkeys([s, s2, strip_accents(s2)]))


def _merge_to_line(geom):
    if isinstance(geom, LineString):
        return geom
    if isinstance(geom, MultiLineString):
        merged = linemerge(geom)
        if isinstance(merged, LineString):
            return merged
        if isinstance(merged, MultiLineString):
            return max(list(merged.geoms), key=lambda g: g.length)
    return None


@st.cache_data(show_spinner=False)
def fetch_street_line(street_name: str, district: int):
    """
    Fetch street polyline (LineString) from OSM within the district.
    Cached by Streamlit to avoid repeated requests.
    """
    if not OSMNX_OK:
        return None

    place = f"District {district}, Ho Chi Minh City, Vietnam"

    for name_try in street_variants(street_name):
        if not name_try:
            continue

        tags = {"highway": True, "name": name_try}

        # OSMnx v2: features_from_place; v1: geometries_from_place
        if hasattr(ox, "features_from_place"):
            gdf = ox.features_from_place(place, tags)
        else:
            gdf = ox.geometries_from_place(place, tags)

        if gdf is None or len(gdf) == 0:
            continue

        gdf = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString"])]
        if gdf.empty:
            continue

        lines = []
        for geom in gdf.geometry:
            line = _merge_to_line(geom)
            if line is not None and line.length > 0:
                lines.append(line)

        if lines:
            return max(lines, key=lambda g: g.length)

    return None


def sample_points_on_line(line, n: int):
    """Sample n random points along a LineString."""
    pts = []
    if line is None or n <= 0:
        return pts
    for _ in range(n):
        d = random.random() * line.length
        p = line.interpolate(d)
        pts.append((float(p.y), float(p.x)))  # (lat, lon)
    return pts


# ------------------------
# Streamlit setup
# ------------------------
st.set_page_config(page_title="Dashboard | RegTech BĐS", layout="wide")
inject_css()
st.title("Dashboard tổng quan (Price Gap & Risk)")

df, _, summary_by_district, top_streets = load_data()

# ------------------------
# Filters
# ------------------------
st.sidebar.header("Bộ lọc")

district_opt = st.sidebar.multiselect("Quận", options=[1, 5], default=[1, 5])

risk_levels = sorted([x for x in df["risk_level"].dropna().unique().tolist() if str(x).strip()])
risk_level_opt = st.sidebar.multiselect("Risk Level", options=risk_levels, default=risk_levels)

aggregation = st.sidebar.radio(
    "Cách hiển thị trên bản đồ",
    options=["Gộp theo (Phường, Đường) để tránh bị dồn điểm", "Hiển thị từng tin đăng"],
    index=0,
)

weight_mode = st.sidebar.selectbox("Trọng số heatmap", options=["Risk Score", "Price Gap"], index=0)

# Heatmap radius in Deck.gl is pixels, not meters
radius_px = st.sidebar.slider("Bán kính heatmap (px)", min_value=20, max_value=150, value=60, step=5)

snap_to_street = st.sidebar.checkbox(
    "Rải điểm theo tuyến đường (OSM) để bám đúng đường",
    value=True,
    disabled=not OSMNX_OK,
)

if not OSMNX_OK:
    st.sidebar.caption("⚠️ Chưa cài osmnx/shapely nên không thể bật chế độ rải theo tuyến đường.")

# Apply filters
dff = df.copy()
dff = dff[dff["District"].isin(district_opt)].copy()
if risk_level_opt:
    dff = dff[dff["risk_level"].astype(str).isin([str(x) for x in risk_level_opt])].copy()

# ------------------------
# Summary
# ------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tin đăng (sau lọc)", f"{len(dff):,}")
c2.metric("Quận đang xem", ", ".join(map(str, district_opt)) if district_opt else "—")
c3.metric("Số phường", f"{dff['Ward'].nunique():,}" if "Ward" in dff.columns else "—")
if set(["District", "ward_norm", "road_norm"]).issubset(set(dff.columns)):
    c4.metric("Số tuyến đường", f"{dff[['District','ward_norm','road_norm']].drop_duplicates().shape[0]:,}")
else:
    c4.metric("Số tuyến đường", "—")

st.divider()

# ------------------------
# Tables
# ------------------------
st.subheader("Top tuyến đường (gợi ý khu vực có chênh lệch cao)")

street_agg = (
    dff.groupby(["District", "Ward", "Street"], dropna=False)
    .agg(
        Listings=("Street", "size"),
        Median_GovPrice=("gov_price_mil_m2", "median"),
        Median_MarketRef=("market_ref_mil_m2", "median"),
        Median_PriceGap=("price_gap", "median"),
        Mean_Risk=("risk_score", "mean"),
        Latitude=("Latitude", "mean"),
        Longitude=("Longitude", "mean"),
    )
    .reset_index()
)

min_n = st.slider("Ngưỡng số tin tối thiểu (n≥)", min_value=1, max_value=50, value=10, step=1)
rank_df = street_agg[street_agg["Listings"] >= min_n].copy().sort_values("Median_PriceGap", ascending=False)
st.dataframe(rank_df.head(30), use_container_width=True)

st.divider()

# ------------------------
# Map (Heatmap)
# ------------------------
st.subheader("Bản đồ nhiệt (heatmap)")

if weight_mode == "Risk Score":
    weight_col = "Mean_Risk" if aggregation.startswith("Gộp") else "risk_score"
    label = "Risk"
else:
    weight_col = "Median_PriceGap" if aggregation.startswith("Gộp") else "price_gap"
    label = "Gap"

if aggregation.startswith("Gộp"):
    map_df = street_agg.copy()
    map_df["weight"] = pd.to_numeric(map_df[weight_col], errors="coerce")
else:
    map_df = dff.copy()
    map_df["weight"] = pd.to_numeric(map_df[weight_col], errors="coerce")

map_df = map_df.dropna(subset=["Latitude", "Longitude", "weight"]).copy()

# ---- Snap to OSM street geometry (street-level only)
if aggregation.startswith("Gộp") and snap_to_street and not map_df.empty:
    keys = map_df[["District", "Street"]].drop_duplicates()
    street_lines = {}

    with st.spinner("Đang truy vấn tuyến đường từ OSM (lần đầu có thể hơi lâu)..."):
        for _, r in keys.iterrows():
            dist = int(r["District"])
            street = str(r["Street"]).strip()
            street_lines[(dist, street)] = fetch_street_line(street, dist)

    snapped_rows = []
    MAX_POINTS_PER_STREET = 40  # cap to keep app fast/clean

    for _, row in map_df.iterrows():
        street = str(row["Street"]).strip()
        dist = int(row["District"])
        k = int(row.get("Listings", 1))
        k = max(1, min(k, MAX_POINTS_PER_STREET))

        line = street_lines.get((dist, street))
        if line is None:
            snapped_rows.append({**row.to_dict()})
        else:
            pts = sample_points_on_line(line, k)
            if not pts:
                snapped_rows.append({**row.to_dict()})
            else:
                for (lat, lon) in pts:
                    new_row = {**row.to_dict()}
                    new_row["Latitude"] = lat
                    new_row["Longitude"] = lon
                    snapped_rows.append(new_row)

    map_df = pd.DataFrame(snapped_rows)

if map_df.empty:
    st.info("Không có đủ dữ liệu tọa độ để vẽ heatmap sau khi lọc.")
else:
    center_lat = float(map_df["Latitude"].mean())
    center_lon = float(map_df["Longitude"].mean())

    heat_layer = pdk.Layer(
        "HeatmapLayer",
        data=map_df,
        get_position=["Longitude", "Latitude"],
        get_weight="weight",
        radiusPixels=radius_px,
        threshold=0.05,
    )

    point_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=["Longitude", "Latitude"],
        get_radius=12,
        radius_units="meters",
        pickable=True,
        auto_highlight=True,
        get_fill_color=[0, 123, 255, 60],
        get_line_color=[0, 90, 200, 80],
        stroked=True,
        filled=True,
    )

    tooltip = {
        "html": "<b>Quận:</b> {District} <br/>"
                "<b>Phường:</b> {Ward} <br/>"
                "<b>Đường:</b> {Street} <br/>"
                f"<b>{label}:</b> " + "{weight}"
    }

    deck = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=13.6,
            pitch=40,
        ),
        layers=[heat_layer, point_layer],
        tooltip=tooltip,
    )

    st.pydeck_chart(deck, use_container_width=True)

st.divider()

# ------------------------
# Extra tables from the data file
# ------------------------
if summary_by_district is not None:
    st.subheader("📎 Summary by District (from data file)")
    st.dataframe(summary_by_district, use_container_width=True)

if top_streets is not None:
    with st.expander("📎 Top Streets (from data file)", expanded=False):
        st.dataframe(top_streets.head(50), use_container_width=True)

st.warning(
    """Lưu ý về heatmap:
- Nếu chưa bật “Rải điểm theo tuyến đường (OSM)”, tọa độ thường chỉ là xấp xỉ theo đường/phường/quận (điểm đại diện).
- Khi bật chế độ OSM, hệ thống truy vấn hình học tuyến đường và rải các điểm mẫu dọc theo tuyến để bản đồ bám theo đường tốt hơn.
- Đây là trực quan hóa ở mức tuyến đường (street-level), không phải số nhà (address-level)."""
)