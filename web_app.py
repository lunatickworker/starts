import streamlit as st
import math
import subprocess
import json
import os
import re

st.set_page_config(
    page_title="Google Maps 평점",
    page_icon="🗺️",
    layout="wide"
)

# 세션 상태 초기화
if "url_input" not in st.session_state:
    st.session_state.url_input = ""
if "current_rating" not in st.session_state:
    st.session_state.current_rating = None
if "current_reviews" not in st.session_state:
    st.session_state.current_reviews = None
if "store_name" not in st.session_state:
    st.session_state.store_name = None

# 동적 제목 표시
if st.session_state.store_name:
    st.title(f"🗺️ {st.session_state.store_name}")
else:
    st.title("🗺️ Google Maps 평점 목표 달성")

# 사이드바에 입력
with st.sidebar:
    st.header("📍 지도 링크 입력")
    
    col1, col2 = st.columns(2)
    with col1:
        extract_button = st.button("🔍 검색하기", key="extract_btn", use_container_width=True)
    with col2:
        clear_button = st.button("🔄 초기화", use_container_width=True)
    
    if clear_button:
        st.session_state.clear()
        st.rerun()
    
    url = st.text_input("Google Maps URL 입력:", key="url_input", value="")

def fetch_map_data_via_scraper(url):
    """scraper.py를 실행해서 rating, reviews, store_name 추출"""
    try:
        script_path = os.path.join(os.path.dirname(__file__), "scraper.py")
        result = subprocess.run(
            ["python", script_path, url],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout.strip())
            return data.get("rating"), data.get("reviews"), data.get("store_name")
        else:
            raise Exception(result.stderr)
    except Exception as e:
        raise Exception(f"추출 오류: {str(e)}")

# 데이터 추출 버튼 클릭
if extract_button:
    if not url:
        st.error("❌ URL을 입력해주세요.")
    else:
        with st.spinner("⏳ 데이터 추출 중..."):
            try:
                rating, reviews, store_name = fetch_map_data_via_scraper(url)
                
                if rating and reviews:
                    st.session_state.current_rating = float(rating)
                    st.session_state.current_reviews = int(reviews.replace(",", ""))
                    st.session_state.store_name = store_name
                    st.success(f"✅ 추출 완료: {rating}⭐ ({reviews}개 리뷰)")
                    st.rerun()
                else:
                    st.error(f"❌ 평점 또는 리뷰수를 찾을 수 없습니다.")
            except Exception as e:
                st.error(f"❌ 오류 발생: {str(e)}")

# 계산 및 표시
if st.session_state.current_rating and st.session_state.current_reviews:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 현재 상태")
        if st.session_state.store_name:
            st.write(f"**🏪 매장명:** {st.session_state.store_name}")
        col1_1, col1_2 = st.columns(2)
        
        with col1_1:
            st.metric("현재 평점", f"{st.session_state.current_rating:.2f}⭐")
        
        with col1_2:
            st.metric("현재 리뷰수", f"{st.session_state.current_reviews:,}개")
    
    # 계산 결과
    with col2:
        st.subheader("🎯 목표 평점별 필요 리뷰수")
        
        target_ratings = [4.95, 4.96, 4.97, 4.98, 4.99]
        results = []
        
        for target_rating in target_ratings:
            # 공식: 필요리뷰수 = [(목표평점×현재리뷰수) - (현재평점×현재리뷰수)] / (5 - 목표평점)
            numerator = (target_rating * st.session_state.current_reviews) - (st.session_state.current_rating * st.session_state.current_reviews)
            denominator = 5 - target_rating
            
            if denominator == 0:
                needed_reviews = float('inf')
            else:
                needed_reviews = numerator / denominator
            
            # 음수인 경우 이미 목표 달성
            if needed_reviews < 0:
                needed_reviews = 0
            
            if needed_reviews == float('inf'):
                needed_text = "불가능"
                cumulative = "N/A"
            else:
                needed_reviews_int = math.ceil(needed_reviews)
                needed_text = f"{needed_reviews_int:,}"
                cumulative_reviews = st.session_state.current_reviews + needed_reviews_int
                cumulative = f"{cumulative_reviews:,}"
            
            results.append({
                "목표 평점": f"⭐ {target_rating:.2f}",
                "필요 리뷰수": needed_text,
                "누적 리뷰수": cumulative
            })
        
        st.dataframe(results, use_container_width=True, hide_index=True)
    
    