"""
할리스커피 전국 매장 위치 및 인구 대비 밀도 지도 생성 스크립트
--------------------------------------------------------------
- 입력 파일:
    source/hollys_store_geo_kakao_final.csv   (매장명, 주소, 위도, 경도 등)
    output/hollys_report.csv                   (시도, 매장수, 인구(만명), 10만명당_매장수)
    source/skorea-provinces-2018-geo.json      (시도 경계선 GeoJSON)
- 출력 파일:
    output/hollys_full_map.html                (개별 매장 마커 + 시도별 색칠 지도)

실행 방법:
    uv run python map_full.py
"""

import os
import json
import pandas as pd
import folium
from folium.plugins import MarkerCluster


# ----------------------------------------------------------------
# 0. 폴더 준비
# ----------------------------------------------------------------
os.makedirs("output", exist_ok=True)


# ----------------------------------------------------------------
# 1. 데이터 불러오기
# ----------------------------------------------------------------
STORE_CSV = "source/hollys_store_geo_kakao_final.csv"
REPORT_CSV = "output/hollys_report.csv"
GEOJSON_PATH = "source/skorea-provinces-2018-geo.json"

if not os.path.exists(STORE_CSV):
    raise FileNotFoundError(
        f"'{STORE_CSV}' 파일이 없습니다. "
        "매장 위경도 데이터(카카오 API로 좌표 변환한 CSV)를 먼저 준비해주세요."
    )

df_store = pd.read_csv(STORE_CSV, encoding="utf-8")

# 위도/경도가 없는(좌표 변환 실패) 매장은 지도에 못 찍으므로 제외
df_store = df_store.dropna(subset=["위도", "경도"])

print(f"지도에 표시할 매장 수: {len(df_store)}개")

# 시도별 밀도 리포트 (선택: 있으면 색칠 레이어까지 같이 그림)
df_report = None
if os.path.exists(REPORT_CSV):
    df_report = pd.read_csv(REPORT_CSV, encoding="utf-8-sig")

geo = None
if os.path.exists(GEOJSON_PATH):
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        geo = json.load(f)


# ----------------------------------------------------------------
# 2. 기본 지도 생성 (대한민국 중심)
# ----------------------------------------------------------------
m = folium.Map(location=[35.9, 127.7], zoom_start=7, tiles="OpenStreetMap")


# ----------------------------------------------------------------
# 3. 시도별 밀도 색칠 레이어 (Choropleth) - 배경으로 깔기
# ----------------------------------------------------------------
if geo is not None and df_report is not None:
    folium.Choropleth(
        geo_data=geo,
        data=df_report,
        columns=["시도", "10만명당_매장수"],
        key_on="feature.properties.name",
        fill_color="YlOrRd",
        fill_opacity=0.5,
        line_opacity=0.3,
        legend_name="10만명당 할리스 매장 수",
        name="시도별 매장 밀도",
    ).add_to(m)


# ----------------------------------------------------------------
# 4. 개별 매장 마커 (MarkerCluster로 성능 확보)
#    - 지도를 움직이거나 확대/축소해도 전체 매장이 클러스터/마커로 계속 표시됨
# ----------------------------------------------------------------
marker_cluster = MarkerCluster(name="전체 매장 위치").add_to(m)

for _, row in df_store.iterrows():
    store_name = row.get("매장명", "이름 없음")
    address = row.get("주소", "")

    popup_html = f"<b>{store_name}</b><br>{address}"

    folium.Marker(
        location=[row["위도"], row["경도"]],
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=store_name,
        icon=folium.Icon(color="darkred", icon="coffee", prefix="fa"),
    ).add_to(marker_cluster)


# ----------------------------------------------------------------
# 5. 레이어 컨트롤 (지도 위에서 색칠/마커 레이어 켜고 끄기 가능)
# ----------------------------------------------------------------
folium.LayerControl(collapsed=False).add_to(m)


# ----------------------------------------------------------------
# 6. 저장
# ----------------------------------------------------------------
OUTPUT_PATH = "output/hollys_full_map.html"
m.save(OUTPUT_PATH)
print(f"저장 완료: {OUTPUT_PATH}")