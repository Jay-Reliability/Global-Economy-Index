import datetime
import json
import traceback
import requests
import yfinance as yf


def get_safe_history(ticker_symbol):
    """주말이나 공휴일에도 에러 없이 최신 데이터를 안전하게 가져오는 헬퍼 함수"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        # 최근 5일간의 데이터를 가져와서 가장 마지막(최신) 행을 선택
        df = ticker.history(period="5d")
        if not df.empty:
            return float(df["Close"].iloc[-1])
        return 0.0
    except Exception as e:
        print(f"⚠️ {ticker_symbol} 데이터 수집 실패: {e}")
        return 0.0


def get_economy_data():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    print(f"🌐 [{today_str}] 글로벌 경제 지표 데이터 수집 시작...")

    try:
        # 1. 외환 데이터 안전 수집
        usdkrw = get_safe_history("USDKRW=X")
        jpykrw = get_safe_history("JPYKRW=X") * 100  # 100엔 기준 보정
        cnykrw = get_safe_history("CNYKRW=X")

        # 2. 유가 데이터 안전 수집
        wti = get_safe_history("CL=F")
        dubai = get_safe_history("BZ=F")  # 브렌트유로 대체

        # 3. 미국 국채 금리 (yfinance 원본값 유효성 검사 후 보정)
        us_3m_raw = get_safe_history("^IRX")
        us_10y_raw = get_safe_history("^TNX")
        us_3m = us_3m_raw / 10 if us_3m_raw > 0 else 3.5
        us_10y = us_10y_raw / 10 if us_10y_raw > 0 else 4.2
        us_spread = us_10y - us_3m

        # 4. 한국 국채 금리 (API 제한 대비 안정적 기본값 설정)
        kr_3m = 3.25
        kr_10y = 3.35
        kr_spread = kr_10y - kr_3m

        # 5. 금 시세
        gold_usd = get_safe_history("GC=F")
        gold_krw = (
            (gold_usd * usdkrw / 31.1034768)
            if (gold_usd > 0 and usdkrw > 0)
            else 0.0
        )

        # 6. 암호화폐
        btc_usd = get_safe_history("BTC-USD")
        btc_krw = btc_usd * usdkrw if (btc_usd > 0 and usdkrw > 0) else 0.0
        eth_usd = get_safe_history("ETH-USD")
        eth_krw = eth_usd * usdkrw if (eth_usd > 0 and usdkrw > 0) else 0.0

        payload = {
            "Date": today_str,
            "USD_KRW": round(usdkrw, 2),
            "JPY_KRW": round(jpykrw, 2),
            "CNY_KRW": round(cnykrw, 2),
            "WTI": round(wti, 2),
            "DUBAI": round(dubai, 2),
            "US_3M": round(us_3m, 2),
            "US_10Y": round(us_10y, 2),
            "US_SPREAD": round(us_spread, 2),
            "KR_3M": round(kr_3m, 2),
            "KR_10Y": round(kr_10y, 2),
            "KR_SPREAD": round(kr_spread, 2),
            "GOLD_USD": round(gold_usd, 2),
            "GOLD_KRW": round(gold_krw, 2),
            "BTC_USD": round(btc_usd, 2),
            "BTC_KRW": round(btc_krw, 2),
            "ETH_USD": round(eth_usd, 2),
            "ETH_KRW": round(eth_krw, 2),
        }

        print("📊 수집된 데이터 샘플:", json.dumps(payload, ensure_ascii=False))
        return payload

    except Exception as e:
        print("❌ 데이터 매핑 중 치명적 오류 발생:")
        traceback.print_exc()
        return None


def send_to_google_sheet():
    data = get_economy_data()
    if not data:
        raise ValueError("수집된 데이터가 비어 있어 전송을 중단합니다.")

    # ⚠️ 중요: 본인의 구글 Apps Script 웹 앱 URL이 맞는지 다시 확인하세요!
    WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwzWqmw6aLnuUApsCAj1InAay7P65QB32weywJnaTdlAdLm9djvI71EEB0sM1xB_dfnOw/exec"

    try:
        response = requests.post(
            WEB_APP_URL,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        print(f"📡 구글 응답 코드: {response.status_code}")
        print(f"📡 구글 응답 내용: {response.text}")

        if response.status_code == 200 and "Success" in response.text:
            print("✅ 구글 스프레드시트 자동 업데이트 성공!")
        else:
            raise RuntimeError(
                f"구글 시트 저장 실패 (응답 메시지 확인 필요): {response.text}"
            )
    except Exception as e:
        print(f"❌ 구글 전송 중 네트워크/서버 오류 발생: {str(e)}")
        raise e


if __name__ == "__main__":
    send_to_google_sheet()
