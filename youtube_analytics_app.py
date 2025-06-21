import streamlit as st
from youtube_service import YouTubeService
from data_utils import process_video_data
from database import save_video_data, load_saved_data
import datetime

def video_search_tab():
    st.header("📺 YouTube 동영상 검색")

    # 사이드바 입력
    search_query = st.sidebar.text_input("검색어", value="Streamlit")
    max_results = st.sidebar.slider("최대 결과 수", min_value=1, max_value=50, value=10)
    order_param = st.sidebar.selectbox("정렬 순서", ["relevance", "date", "viewCount", "rating"])
    duration_param = st.sidebar.selectbox("영상 길이", ["any", "short", "medium", "long"])
    language = st.sidebar.text_input("언어 코드 (예: en, ko, ja)", value="ko")
    region = st.sidebar.text_input("국가 코드 (예: KR, US, JP)", value="KR")

    today = datetime.date.today()
    days_ago = st.sidebar.slider("며칠 전부터 검색할까요?", min_value=0, max_value=30, value=7)
    published_after = (today - datetime.timedelta(days=days_ago)).isoformat() + "T00:00:00Z"

    # 서비스 객체 생성
    youtube_service = YouTubeService()

    if st.button("🔍 검색"):
        try:
            videos = youtube_service.search_videos(
                query=search_query,
                max_results=max_results,
                duration=duration_param,
                published_after=published_after,
                order=order_param,
                relevance_language=language,
                region_code=region
            )
            st.success(f"총 {len(videos)}개의 동영상을 찾았습니다.")

            video_ids = [video["id"]["videoId"] for video in videos]
            details = youtube_service.get_video_details(video_ids)
            df = process_video_data(details)

            st.dataframe(df)

            if st.button("💾 데이터 저장"):
                save_video_data(df)
                st.success("데이터가 저장되었습니다.")

        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")

def saved_data_tab():
    st.header("💾 저장된 데이터")
    data = load_saved_data()
    if data is not None:
        st.dataframe(data)
    else:
        st.info("저장된 데이터가 없습니다.")

def main():
    st.set_page_config(page_title="YouTube 분석 앱", layout="wide")
    st.title("📊 유튜브 채널 & 동영상 분석 앱")

    tab = st.sidebar.radio("탭 선택", ["동영상 검색", "저장된 데이터 보기"])
    if tab == "동영상 검색":
        video_search_tab()
    elif tab == "저장된 데이터 보기":
        saved_data_tab()

if __name__ == "__main__":
    main()
