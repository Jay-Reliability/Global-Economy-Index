import datetime
import json
import requests
import yfinance as yf


def get_economy_data():
    # 1. 기준 날짜 (오늘)
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # 2. Yahoo Finance 및 대안 API를 통한 데이터 수집
    # ⚠️ 주말이나 장 개시 전 데이터 공백을 방지하기 위해 최신 1개 데이터를 가져옵니다.
    try:
        # 환율 (원달러, 원엔, 원위안)
        usdkrw = yf.Ticker("USDKRW=X").history(period="1d")["Close"].iloc[-1]
        jpykrw = (
            yf.Ticker("JPYKRW=X").history(period="1d")["Close"].iloc[-1] * 100
        )  # 100엔 기준 보정
        cnykrw = yf.Ticker("CNYKRW=X").history(period="1d")["Close"].iloc[-1]

        # 유가
        wti = yf.Ticker("CL=F").history(period="1d")["Close"].iloc[-1]
        dubai = yf.Ticker("BZ=F").history(period="1d")[
            "Close"
        ].iloc[-1]  # 브렌트유로 대체하거나 두바이유 제공 API 연동 가능

        # 미국 국채 금리
        us_3m = (
            yf.Ticker("^IRX").history(period="1d")["Close"].iloc[-1] / 10
        )  # 단기(3개월)
        us_10y = (
            yf.Ticker("^TNX").history(period="1d")["Close"].iloc[-1] / 10
        )  # 장기(10년)
        us_spread = us_10y - us_3m  # 장단기 금리차

        # 한국 국채 금리 (대안 데이터 혹은 고정 샘플링 - yfinance에 한국 국채는 제한적이므로 에러 방지 처리)
        kr_3m = 3.25  # 실제 운영시 한국은행 API 또는 인베스팅 스크래핑 연동 권장
        kr_10y = 3.35
        kr_spread = kr_10y - kr_3m

        # 금 (미국 USD, 한국 KRW)
        gold_usd = yf.Ticker("GC=F").history(period="1d")["Close"].iloc[-1]
        gold_krw = gold_usd * usdkrw / 31.1034768  # 트로이온스당 가격을 g당 원화로 환산(예시)

        # 암호화폐 (비트코인, 이더리움)
        btc_usd = yf.Ticker("BTC-USD").history(period="1d")["Close"].iloc[-1]
        btc_krw = btc_usd * usdkrw
        eth_usd = yf.Ticker("ETH-USD").history(period="1d")["Close"].iloc[-1]
        eth_krw = eth_usd * usdkrw

        # 18개 컬럼 순서대로 딕셔너리 매핑
        payload = {
            "Date": today_str,
            "USD_KRW": float(round(usdkrw, 2)),
            "JPY_KRW": float(round(jpykrw, 2)),
            "CNY_KRW": float(round(cnykrw, 2)),
            "WTI": float(round(wti, 2)),
            "DUBAI": float(round(dubai, 2)),
            "US_3M": float(round(us_3m, 2)),
            "US_10Y": float(round(us_10y, 2)),
            "US_SPREAD": float(round(us_spread, 2)),
            "KR_3M": float(round(kr_3m, 2)),
            "KR_10Y": float(round(kr_10y, 2)),
            "KR_SPREAD": float(round(kr_spread, 2)),
            "GOLD_USD": float(round(gold_usd, 2)),
            "GOLD_KRW": float(round(gold_krw, 2)),
            "BTC_USD": float(round(btc_usd, 2)),
            "BTC_KRW": float(round(btc_krw, 2)),
            "ETH_USD": float(round(eth_usd, 2)),
            "ETH_KRW": float(round(eth_krw, 2)),
        }
        return payload
    except Exception as e:
        print(f"데이터 수집 중 오류 발생: {e}")
        return None


def send_to_google_sheet():
    # 1단계: 데이터 수집
    data = get_economy_data()
    if not data:
        return

    # 구글 Apps Script 웹 앱 URL (Step 2의 URL 사용)
    WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwzWqmw6aLnuUApsCAj1InAay7P65QB32weywJnaTdlAdLm9djvI71EEB0sM1xB_dfnOw/exec"

    # 2단계: POST 요청 전송
    try:
        response = requests.post(
            WEB_APP_URL,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )
        if response.status_code == 200:
            print("✅ 구글 스프레드시트 자동 업데이트 성공!")
        else:
            print(f"❌ 전송 실패 (오류 코드: {response.status_code})")

if __name__ == "__main__":
    send_to_google_sheet()
