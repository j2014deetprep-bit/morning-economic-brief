import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta


# ============================================================
# 설정
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%m/%d")


# ============================================================
# Google News RSS 검색
# ============================================================

def get_news(query, limit=5):
    encoded = urllib.parse.quote(query)

    url = (
        "https://news.google.com/rss/search?"
        f"q={encoded}&hl=ko&gl=KR&ceid=KR:ko"
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read()

        root = ET.fromstring(data)

        articles = []

        for item in root.findall(".//item")[:limit]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "").strip()

            if title:
                articles.append({
                    "title": title,
                    "link": link,
                    "date": pub_date
                })

        return articles

    except Exception as e:
        print(f"뉴스 수집 오류: {e}")
        return []


# ============================================================
# 섹션별 뉴스 검색
# ============================================================

def collect_news():

    stock = []

    stock_queries = [
        "코스피 코스닥 증시",
        "삼성전자 SK하이닉스 주식",
        "미국 증시 나스닥 S&P500",
        "반도체 AI 주식",
    ]

    for query in stock_queries:
        stock.extend(get_news(query, 3))

    economy = []

    economy_queries = [
        "한국 경제 금리 환율",
        "한국은행 기준금리",
        "원달러 환율 경제",
        "한국 물가 부동산",
        "정부 경제 정책",
    ]

    for query in economy_queries:
        economy.extend(get_news(query, 3))

    companies = []

    company_queries = [
        "삼성전자 기업",
        "SK하이닉스 기업",
        "현대차 기업",
        "LG전자 기업",
        "국내 기업 실적 투자",
    ]

    for query in company_queries:
        companies.extend(get_news(query, 3))

    return {
        "stock": stock,
        "economy": economy,
        "companies": companies
    }


# ============================================================
# 중복 기사 제거
# ============================================================

def unique_articles(articles, limit=10):

    result = []
    titles = set()

    for article in articles:

        title = article["title"]

        # Google News 제목에 붙는 언론사명을 제외한
        # 대략적인 중복 제거
        clean_title = title.split(" - ")[0].strip()

        if clean_title in titles:
            continue

        titles.add(clean_title)
        result.append(article)

        if len(result) >= limit:
            break

    return result


# ============================================================
# Telegram 메시지 전송
# ============================================================

def send_telegram(message):

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": "true"
    }).encode()

    request = urllib.request.Request(
        url,
        data=data,
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = response.read().decode()

    print(result)


# ============================================================
# 기사 목록을 메시지로 변환
# ============================================================

def format_articles(articles):

    text = ""

    for i, article in enumerate(articles, 1):

        title = article["title"]
        link = article["link"]

        text += f"{i}. {title}\n"
        text += f"   {link}\n\n"

    return text


# ============================================================
# 메인
# ============================================================

def main():

    news = collect_news()

    stock = unique_articles(news["stock"], 8)
    economy = unique_articles(news["economy"], 8)
    companies = unique_articles(news["companies"], 8)

    message = f"""
☀️ {TODAY} 아침 경제 브리핑

━━━━━━━━━━━━━━
📈 1. 주식 브리핑
━━━━━━━━━━━━━━

전일 미국 증시와 국내 증시에 영향을 줄 만한 주요 뉴스입니다.

{format_articles(stock)}

━━━━━━━━━━━━━━
💰 2. 경제동향
━━━━━━━━━━━━━━

금리·환율·물가·부동산·정부 정책 관련 주요 뉴스입니다.

{format_articles(economy)}

━━━━━━━━━━━━━━
🏢 3. 기업동향
━━━━━━━━━━━━━━

국내 주요 기업과 산업 관련 주요 뉴스입니다.

{format_articles(companies)}

━━━━━━━━━━━━━━
📌 참고
━━━━━━━━━━━━━━

이 브리핑은 공개 RSS 뉴스의 최신 기사를 자동 수집해
정리한 것입니다.

기사 제목과 실제 내용에는 차이가 있을 수 있으므로
중요한 투자 판단은 원문을 확인하세요.
"""

    # Telegram 메시지는 4096자 제한이 있으므로
    # 너무 길 경우 잘라낸다.
    if len(message) > 4000:
        message = message[:3950] + "\n\n[이하 생략]"

    send_telegram(message)


if __name__ == "__main__":
    main()
