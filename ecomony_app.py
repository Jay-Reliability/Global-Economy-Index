import datetime
import json
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# =================================================================
# [설정] 구글 스프레드시트 기반 URL 정보
# =================================================================
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwzWqmw6aLnuUApsCAj1InAay7P65QB32weywJnaTdlAdLm9djvI71EEB0sM1xB_dfnOw/exec"

NEW_SHEET_ID = "1_F0_agopnMOKkKiJgWQEr68fVDFdXKt1pCjcTSBVgm4"
READ_URL = f"https://docs.google.com/spreadsheets/d/{NEW_SHEET_ID}/gviz/tq?tqx=out:csv"
# =================================================================

st.set_page_config(page_title="Global Economy Index", layout="wide")
st.title("🌐 Global Economy Index Dashboard")
st.markdown("매일 19시 자동으로 수집된 글로벌 주요 경제 지표를 실시간 모니터링합니다.")
st.markdown("---")

# 18개 컬럼 양식 표준화 정의
COLUMNS_LIST = [
    "Date",
    "USD-KRW 환율",
    "JPY-KRW 환율",
    "CNY-KR 환율",
    "미국 WTI 유가",
    "중동 두바이 유가",
    "단기국채금리(US)",
    "10년 장기국채금리(US)",
    "장단기금리차(US)",
    "단기국채금리(KR)",
    "10년 장기국채금리(KR)",
    "장단기금리차(KR)",
    "Gold(US)",
    "Gold(KRW)",
    "비트코인(USD)",
    "비트코인(KRW)",
    "이더리움(USD)",
    "이더리움(KRW)",
]


@st.cache_data(ttl=5)
def load_data():
    try:
        df = pd.read_csv(READ_URL)
        if df.empty or "Date" not in df.columns:
            return pd.DataFrame(columns=COLUMNS_LIST)

        # 구글 시트 데이터 컬럼 강제 동기화 (18개 항목)
        df.columns = COLUMNS_LIST
        return df
    except Exception as e:
        st.sidebar.error(f"데이터 로드 실패: {str(e)}")
        return pd.DataFrame(columns=COLUMNS_LIST)


data = load_data()

if not data.empty and len(data) > 0:
    # 데이터 전처리
    data = data.dropna(subset=["Date"])
    data["Date"] = pd.to_datetime(data["Date"])
    data = data.sort_values("Date")

    # 최신 지표 요약 (KPI 레이아웃)
    latest = data.iloc[-1]
    st.subheader("📍 최신 주요 지표 요약")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(label="💵 원/달러 환율", value=f"{latest['USD-KRW 환율']:,} 원")
    kpi2.metric(label="🛢️ 미국 WTI 유가", value=f"${latest['미국 WTI 유가']:,}")

    # 💡 [보정 완료] '장단기금리차(US)'의 오타(닫는 괄호 누락)를 수정했습니다.
    kpi3.metric(
        label="📉 장단기금리차(US)", value=f"{latest['장단기금리차(US)']}%"
    )

    # 숫자가 들어올 경우 대비하여 포맷팅 안전성 강화
    btc_val = latest["비트코인(KRW)"]
    try:
        btc_display = f"{float(btc_val) / 10000:,.1f} 만원"
    except:
        btc_display = f"{btc_val} 원"

    kpi4.metric(label="🪙 비트코인(KRW)", value=btc_display)

    st.markdown("---")

    # 트렌드 분석 탭 분할
    st.subheader("📈 부문별 트렌드 분석")
    tab1, tab2, tab3, tab4 = st.tabs(
        ["💱 외환 (환율)", "🔥 에너지가/원자재", "🏦 금리 (국채)", "🚀 크립토 (가상자산)"]
    )

    with tab1:
        fig_fx = px.line(
            data,
            x="Date",
            y=["USD-KRW 환율", "JPY-KRW 환율", "CNY-KR 환율"],
            title="주요국 통화 대비 원화 환율 추이",
            markers=True,
        )
        st.plotly_chart(fig_fx, use_container_width=True)

    with tab2:
        col_a, col_b = st.columns(2)
        with col_a:
            fig_oil = px.line(
                data,
                x="Date",
                y=["미국 WTI 유가", "중동 두바이 유가"],
                title="국제 유가 추이 ($/배럴)",
                markers=True,
            )
            st.plotly_chart(fig_oil, use_container_width=True)
        with col_b:
            fig_gold = px.line(
                data,
                x="Date",
                y=["Gold(US)", "Gold(KRW)"],
                title="국제/국내 금 시세 추이",
                markers=True,
            )
            st.plotly_chart(fig_gold, use_container_width=True)

    with tab3:
        col_c, col_d = st.columns(2)
        with col_c:
            fig_us_bond = px.line(
                data,
                x="Date",
                y=["단기국채금리(US)", "10년 장기국채금리(US)", "장단기금리차(US)"],
                title="미국 국채 금리 및 장단기 금리차 추이",
                markers=True,
            )
            st.plotly_chart(fig_us_bond, use_container_width=True)
        with col_d:
            fig_kr_bond = px.line(
                data,
                x="Date",
                y=["단기국채금리(KR)", "10년 장기국채금리(KR)", "장단기금리차(KR)"],
                title="한국 국채 금리 및 장단기 금리차 추이",
                markers=True,
            )
            st.plotly_chart(fig_kr_bond, use_container_width=True)

    with tab4:
        fig_crypto = px.line(
            data,
            x="Date",
            y=["비트코인(USD)", "이더리움(USD)"],
            title="주요 가상자산 가격 추이 (USD)",
            markers=True,
        )
        st.plotly_chart(fig_crypto, use_container_width=True)

    # 전체 데이터 테이블
    with st.expander("📊 18개 경제지표 전체 기록 데이터 확인"):
        st.dataframe(data, use_container_width=True)
else:
    st.warning("⚠️ 아직 대시보드에 표시할 누적 데이터가 없습니다.")
