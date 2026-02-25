import asyncio
import time
import sys
import json
import urllib.parse
import re
import subprocess

# Playwright 자동 설치
try:
    from playwright.async_api import async_playwright
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium", "--with-deps"], check=True)
    from playwright.async_api import async_playwright

# UTF-8 인코딩으로 설정
sys.stdout.reconfigure(encoding='utf-8')

async def main(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        
        # 최종 리다이렉션 URL에서 매장명 추출
        final_url = page.url
        store_name = None
        
        if "/maps/place/" in final_url:
            try:
                parts = final_url.split("/maps/place/")
                if len(parts) > 1:
                    store_part = parts[1].split("/")[0]
                    # URL 인코딩 해제 (+ 를 공백으로 변환)
                    store_name = urllib.parse.unquote_plus(store_part)
                    # | 기호로 구분된 부분 중 첫 번째 부분만 추출
                    if "|" in store_name:
                        store_name = store_name.split("|")[0].strip()
                    else:
                        store_name = store_name.strip()
                    
                    # 한글이 있으면 사용, 없으면 None으로 설정 (페이지에서 추출)
                    if not any('\uac00' <= char <= '\ud7af' for char in store_name):
                        store_name = None
            except Exception as e:
                store_name = None
        
        # 페이지가 완전히 로드될 때까지 대기
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass
        
        time.sleep(5)  # 추가 대기 (더 길게)
        
        # URL에서 한글 매장명을 찾지 못한 경우 페이지에서 추출
        if not store_name:
            try:
                # h1 태그에서 매장명 찾기
                h1_elements = await page.locator("h1").all_text_contents()
                if h1_elements:
                    store_name = h1_elements[0].strip()
            except:
                pass
            
            # h1이 없으면 page title에서 추출
            if not store_name:
                try:
                    page_title = await page.title()
                    # " - Google Maps" 부분 제거
                    if " - Google Maps" in page_title:
                        store_name = page_title.replace(" - Google Maps", "").strip()
                    else:
                        store_name = page_title.strip()
                except:
                    pass

        # 모든 텍스트 콘텐츠 추출 (span, div, button 등)
        all_elements = await page.locator("span, div, button, a").all_text_contents()
        
        rating = None
        reviews = None

        for text in all_elements:
            text = text.strip()
            if not text:
                continue
                
            # 평점: 소수점 포함 숫자 (예: 4.9, 4.95)
            if rating is None:
                if "." in text:
                    try:
                        fval = float(text)
                        if 0 <= fval <= 5:
                            rating = text
                    except:
                        pass
            
            # 리뷰 수: 괄호 안 숫자 또는 쉼표 포함 숫자 (예: (43), 1,234)
            if reviews is None:
                if text.startswith("(") and text.endswith(")"):
                    inner = text.strip("()").replace(",", "")
                    if inner.isdigit():
                        reviews = inner
                elif text.replace(",", "").isdigit() and len(text) > 0:
                    # 리뷰 수가 충분히 크면 저장
                    try:
                        num = int(text.replace(",", ""))
                        if num > 5:  # 최소 5개 이상의 리뷰
                            reviews = text
                    except:
                        pass

            # 둘 다 찾으면 루프 종료
            if rating and reviews:
                break

        await browser.close()

        # JSON으로 출력
        result = {"rating": rating, "reviews": reviews, "store_name": store_name}
        print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    url = sys.argv[1]
    asyncio.run(main(url))
