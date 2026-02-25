#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
필요한 리뷰 수 계산 프로그램 (Flask 웹 버전)
공식: 필요 리뷰수 = (목표평점수×현재리뷰수) - (현재평점수×현재리뷰수) / (5 - 목표평점수)
"""

import asyncio
import re
from threading import Thread
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

app = Flask(__name__)

# CSP 헤더 설정
@app.after_request
def set_csp_header(response):
    response.headers['Content-Security-Policy'] = "script-src 'self'"
    return response

async def parse_google_maps_url(url):
    """Google Maps에서 평점과 리뷰 수 파싱 (다중 방법)"""
    try:
        rating = None
        reviews = None
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
            page = await browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # 페이지 로드
            try:
                await page.goto(url, timeout=60000, wait_until="load")
            except:
                print("⚠ 페이지 로드 타임아웃 (계속 진행)")
            
            # 충분한 시간 대기
            await page.wait_for_timeout(5000)
            
            # 페이지 제목 확인
            page_title = await page.title()
            print(f"📄 페이지 제목: {page_title}")
            
            # 평점 추출
            try:
                rating_js = """
                (function() {
                    var xpath = "/html/body/div[1]/div[2]/div[9]/div[8]/div/div/div[1]/div[3]/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div[2]/div/div[1]/div[2]/span[1]/span[1]";
                    var result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                    var el = result.singleNodeValue;
                    if (el) {
                        return el.textContent.trim();
                    }
                    return null;
                })();
                """
                rating_text = await page.evaluate(rating_js)
                if rating_text:
                    match = re.search(r"(\d+\.?\d*)", str(rating_text))
                    if match:
                        rating = float(match.group(1))
                        print(f"✓ 평점 추출 성공: {rating}")
                else:
                    print(f"⚠ 평점 XPath 결과: null, 대체 방법 시도 중...")
                    span_search = """
                    (function() {
                        var spans = document.querySelectorAll('span');
                        for (var i = 0; i < spans.length; i++) {
                            var text = spans[i].textContent.trim();
                            var num = parseFloat(text);
                            if (/^\\d+\\.?\\d*$/.test(text) && num >= 0 && num <= 5) {
                                if (text.length < 5) return text;
                            }
                        }
                        return null;
                    })();
                    """
                    rating_alt = await page.evaluate(span_search)
                    if rating_alt:
                        rating = float(rating_alt)
                        print(f"✓ 평점 대체 방법 성공: {rating}")
                    else:
                        print(f"✗ 평점 요소를 찾을 수 없습니다")
            except Exception as e:
                print(f"❌ 평점 추출 오류: {e}")
            
            # 리뷰 수 추출
            try:
                reviews_js = """
                (function() {
                    var xpath = "/html/body/div[1]/div[2]/div[9]/div[8]/div/div/div[1]/div[3]/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div[2]/div/div[1]/div[2]/span[2]/span/span";
                    var result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                    var el = result.singleNodeValue;
                    if (el) {
                        return el.textContent.trim();
                    }
                    return null;
                })();
                """
                reviews_text = await page.evaluate(reviews_js)
                if reviews_text:
                    match = re.search(r"(\d+)", str(reviews_text).replace(",", ""))
                    if match:
                        reviews = int(match.group(1))
                        print(f"✓ 리뷰 수 추출 성공: {reviews}")
                else:
                    print(f"⚠ 리뷰 XPath 결과: null, 대체 방법 시도 중...")
                    aria_search = """
                    (function() {
                        var spans = document.querySelectorAll('span[aria-label]');
                        for (var i = 0; i < spans.length; i++) {
                            var label = spans[i].getAttribute('aria-label');
                            if (label && label.toLowerCase().includes('review')) {
                                var match = label.match(/\\d+/);
                                if (match) return match[0];
                            }
                        }
                        return null;
                    })();
                    """
                    reviews_alt = await page.evaluate(aria_search)
                    if reviews_alt:
                        reviews = int(reviews_alt)
                        print(f"✓ 리뷰 수 대체 방법 성공: {reviews}")
                    else:
                        print(f"✗ 리뷰 요소를 찾을 수 없습니다")
            except Exception as e:
                print(f"❌ 리뷰 수 추출 오류: {e}")
            
            await browser.close()
            print(f"최종 결과 - 평점: {rating}, 리뷰 수: {reviews}")
            return rating, reviews
        
    except Exception as e:
        print(f"파싱 오류: {e}")
        import traceback
        traceback.print_exc()
        return None, None

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/parse', methods=['POST'])
def api_parse():
    """Google Maps 파싱 API"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL을 입력하세요.'})
        
        # URL 유효성 검사
        if not url.startswith("http://") and not url.startswith("https://"):
            return jsonify({'success': False, 'error': '유효한 URL이 아닙니다. (http:// 또는 https://로 시작해야 합니다)'})
        
        if not ("maps.google.com" in url or "google.com/maps" in url):
            return jsonify({'success': False, 'error': '유효한 Google Maps 링크가 아닙니다.'})
        
        # 비동기 파싱 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        rating, reviews = loop.run_until_complete(parse_google_maps_url(url))
        loop.close()
        
        if rating is not None or reviews is not None:
            return jsonify({
                'success': True,
                'rating': rating,
                'reviews': reviews
            })
        else:
            return jsonify({'success': False, 'error': '페이지에서 평점/리뷰 수를 찾을 수 없습니다.'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'파싱 중 오류 발생: {str(e)}'})

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    """리뷰 수 계산 API"""
    try:
        data = request.json
        current_rating = float(data.get('current_rating', 0))
        current_reviews = float(data.get('current_reviews', 0))
        target_rating = float(data.get('target_rating', 0))
        
        # 검증
        if not (0 <= current_rating <= 5):
            return jsonify({'success': False, 'error': '현재 평점은 0~5 사이여야 합니다.'})
        
        if current_reviews < 0:
            return jsonify({'success': False, 'error': '현재 리뷰 수는 0 이상이어야 합니다.'})
        
        if not (0 <= target_rating < 5):
            return jsonify({'success': False, 'error': '목표 평점은 0~5 사이(5 제외)여야 합니다.'})
        
        # 계산
        numerator = (target_rating * current_reviews) - (current_rating * current_reviews)
        denominator = 5 - target_rating
        
        required_reviews = numerator / denominator
        
        # 결과 생성
        if required_reviews > 0:
            result = f"필요 리뷰: {int(required_reviews)}개"
        elif required_reviews < 0:
            result = "목표 평점 달성! 🎉"
        else:
            result = "목표 평점과 동일"
        
        return jsonify({
            'success': True,
            'required_reviews': required_reviews,
            'result': result
        })
    
    except ValueError:
        return jsonify({'success': False, 'error': '올바른 숫자를 입력해주세요.'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'계산 중 오류 발생: {str(e)}'})

if __name__ == '__main__':
    print("서버 시작: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
