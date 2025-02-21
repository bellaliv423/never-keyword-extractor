import streamlit as st
import os
from dotenv import load_dotenv

# 환경변수 로딩을 가장 먼저
try:
    if 'NAVER_CLIENT_ID' in st.secrets:
        os.environ['NAVER_CLIENT_ID'] = st.secrets['NAVER_CLIENT_ID']
        os.environ['NAVER_CLIENT_SECRET'] = st.secrets['NAVER_CLIENT_SECRET']
        os.environ['OPENAI_API_KEY'] = st.secrets['OPENAI_API_KEY']
    else:
        load_dotenv()
except Exception as e:
    st.error(f"환경변수 로딩 오류: {str(e)}")

# 나머지 imports
from modules.naver_crawler import NaverCrawler
from modules.content_processor import ContentProcessor
from modules.content_uploader import ContentUploader
import time
from datetime import datetime
import json
import asyncio
from streamlit.runtime.scriptrunner import add_script_run_ctx

# 1. 기본 레이아웃 설정
st.set_page_config(
    page_title="스마트 키워드 콘텐츠 추출기",
    page_icon="📰",
    layout="wide"
)

# 2. 스타일 설정
style = """
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .output-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .stSelectbox {
        margin: 1rem 0;
    }
    .stExpander {
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .css-1d391kg {
        padding: 1rem;
    }
</style>
"""
st.markdown(style, unsafe_allow_html=True)

# 세션 상태 초기화
if 'init' not in st.session_state:
    st.session_state.init = True
    st.session_state.search_history = []
    st.session_state.last_search = None
    st.session_state.processing_state = None
    
    try:
        # 크롤러 초기화
        st.session_state.crawler = NaverCrawler()
        st.session_state.uploader = ContentUploader()
        st.success("시스템이 성공적으로 초기화되었습니다.")
    except APIKeyError as e:
        st.error("API 키 오류가 발생했습니다.")
        st.error(str(e))
        st.info("네이버 API 키를 확인해주세요.")
        st.session_state.crawler = None
        st.session_state.uploader = None
    except Exception as e:
        st.error("초기화 중 오류가 발생했습니다.")
        st.error(str(e))
        st.session_state.crawler = None
        st.session_state.uploader = None

# 사이드바 구성
with st.sidebar:
    st.title("⚙️ 설정")
    
    with st.expander("📊 검색 설정", expanded=True):
        news_count = st.slider(
            "뉴스 검색 수",
            min_value=5,
            max_value=20,
            value=10,
            help="검색할 뉴스 기사의 수를 설정합니다."
        )
        
        blog_count = st.slider(
            "블로그 검색 수",
            min_value=3,
            max_value=10,
            value=5,
            help="검색할 블로그 포스트의 수를 설정합니다."
        )
    
    with st.expander("🤖 AI 처리 설정", expanded=True):
        ai_mode = st.selectbox(
            "처리 모드",
            options=["요약", "재구성"],
            help="AI가 콘텐츠를 처리하는 방식을 선택합니다."
        )
    
    with st.expander("💾 저장 설정", expanded=True):
        save_platforms = st.multiselect(
            "저장 플랫폼",
            options=["옵시디언", "노션"],
            default=["옵시디언"],
            help="처리된 콘텐츠를 저장할 플랫폼을 선택합니다."
        )

# 메인 화면
st.title("📰 스마트 키워드 콘텐츠 추출기")
st.markdown("---")

# 검색 및 결과 영역
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🔍 키워드 검색")
    keyword = st.text_input(
        "검색 키워드",
        placeholder="검색할 키워드를 입력하세요",
        help="뉴스와 블로그에서 검색할 키워드를 입력합니다."
    )
    
    if st.button("검색 시작", use_container_width=True):
        if not keyword:
            st.error("키워드를 입력해주세요!")
        else:
            with st.spinner("🔍 콘텐츠를 검색하고 있습니다..."):
                try:
                    # 크롤러 상태 확인
                    if st.session_state.crawler is None:
                        st.session_state.crawler = NaverCrawler()
                    
                    # 진행 상태 표시
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 뉴스 검색
                    status_text.text("뉴스 검색 중...")
                    progress_bar.progress(20)
                    news_results = st.session_state.crawler.get_news_articles(keyword, news_count)
                    st.session_state.news_results = news_results
                    
                    # 블로그 검색
                    status_text.text("블로그 검색 중...")
                    progress_bar.progress(50)
                    blog_results = st.session_state.crawler.get_blog_contents(keyword, blog_count)
                    st.session_state.blog_results = blog_results
                    
                    # 연관 키워드 검색
                    status_text.text("연관 키워드 검색 중...")
                    progress_bar.progress(80)
                    related_keywords = st.session_state.crawler.get_related_keywords(keyword)
                    st.session_state.related_keywords = related_keywords
                    
                    progress_bar.progress(100)
                    status_text.empty()
                    
                    # 결과 처리
                    if not news_results and not blog_results:
                        st.warning("검색 결과가 없습니다.")
                    else:
                        result_count = len(news_results) + len(blog_results)
                        st.success(f"검색이 완료되었습니다! (총 {result_count}개의 결과)")
                    
                except APIKeyError as e:
                    st.error("API 키 오류가 발생했습니다.")
                    st.error(str(e))
                    st.info("네이버 API 키를 확인해주세요.")
                    
                except ConnectionError as e:
                    st.error("네트워크 연결 오류가 발생했습니다.")
                    st.error(str(e))
                    st.info("인터넷 연결을 확인해주세요.")
                    
                except Exception as e:
                    st.error("예상치 못한 오류가 발생했습니다.")
                    st.error(str(e))
                    st.exception(e)

with col2:
    st.subheader("📊 검색 결과")
    
    # 결과 탭
    tab1, tab2, tab3 = st.tabs(["📰 뉴스", "📝 블로그", "🔄 연관 키워드"])
    
    with tab1:
        if 'news_results' in st.session_state:
            for article in st.session_state.news_results:
                with st.container():
                    st.markdown(f"### [{article['title']}]({article['link']})")
                    st.markdown(article['description'])
                    if article['tags']:
                        st.markdown(' '.join(article['tags']))
                    st.markdown("---")
    
    with tab2:
        if 'blog_results' in st.session_state:
            for post in st.session_state.blog_results:
                with st.container():
                    st.markdown(f"### [{post['title']}]({post['link']})")
                    st.markdown(post['description'])
                    if post['tags']:
                        st.markdown(' '.join(post['tags']))
                    st.markdown("---")
    
    with tab3:
        if 'related_keywords' in st.session_state:
            st.markdown("### 연관 키워드")
            keywords_html = ' '.join([
                f'<span style="background-color: #f0f2f6; padding: 0.2rem 0.5rem; border-radius: 1rem; margin: 0.2rem;">{k}</span>'
                for k in st.session_state.related_keywords
            ])
            st.markdown(keywords_html, unsafe_allow_html=True)

# AI 처리 섹션
st.markdown("---")
st.subheader("🤖 AI 처리")

# 콘텐츠 선택
if 'news_results' in st.session_state or 'blog_results' in st.session_state:
    all_contents = []
    if 'news_results' in st.session_state:
        all_contents.extend([{'type': 'news', **item} for item in st.session_state.news_results])
    if 'blog_results' in st.session_state:
        all_contents.extend([{'type': 'blog', **item} for item in st.session_state.blog_results])
    
    # 콘텐츠 선택 UI
    selected_title = st.selectbox(
        "처리할 콘텐츠 선택",
        options=[item['title'] for item in all_contents],
        format_func=lambda x: f"[{next(item['type'] for item in all_contents if item['title'] == x)}] {x}"
    )
    
    selected_content = next(item for item in all_contents if item['title'] == selected_title)
    
    # 처리 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 AI 처리 시작", use_container_width=True):
            with st.spinner("AI가 콘텐츠를 처리하고 있습니다..."):
                try:
                    processor = ContentProcessor()
                    # 비동기 함수 실행을 위한 이벤트 루프 설정
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    # 컨텍스트 추가
                    add_script_run_ctx()
                    # 비동기 처리 실행
                    result = loop.run_until_complete(
                        processor.process_content(selected_content, mode=ai_mode)
                    )
                    st.session_state.ai_result = result
                    st.success("처리가 완료되었습니다!")
                except Exception as e:
                    st.error(f"처리 중 오류가 발생했습니다: {str(e)}")
                finally:
                    loop.close()

# 결과 표시
if 'ai_result' in st.session_state:
    st.markdown("---")
    st.subheader("📝 처리 결과")
    
    if st.session_state.ai_result['type'] == 'summary':
        with st.expander("1000자 버전", expanded=True):
            st.markdown(st.session_state.ai_result['long_version'])
            if st.button("📋 복사 (1000자)", key="copy_long"):
                st.session_state.uploader.copy_to_clipboard(st.session_state.ai_result['long_version'])
                st.success("복사되었습니다!")
        
        with st.expander("450자 버전"):
            st.markdown(st.session_state.ai_result['short_version'])
            if st.button("📋 복사 (450자)", key="copy_short"):
                st.session_state.uploader.copy_to_clipboard(st.session_state.ai_result['short_version'])
                st.success("복사되었습니다!")
    
    else:  # restructured
        with st.expander("재구성 결과", expanded=True):
            st.markdown(st.session_state.ai_result['content'])
            if st.button("📋 복사", key="copy_restructured"):
                st.session_state.uploader.copy_to_clipboard(st.session_state.ai_result['content'])
                st.success("복사되었습니다!")
    
    # 키워드 표시
    if 'keywords' in st.session_state.ai_result:
        st.markdown("### 추출된 키워드")
        keywords_html = ' '.join([
            f'<span style="background-color: #f0f2f6; padding: 0.2rem 0.5rem; border-radius: 1rem; margin: 0.2rem;">{k}</span>'
            for k in st.session_state.ai_result['keywords']
        ])
        st.markdown(keywords_html, unsafe_allow_html=True)

    # 저장 기능 추가
    st.markdown("---")
    st.subheader("💾 저장")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 클립보드에 복사", use_container_width=True):
            try:
                content = st.session_state.ai_result['content'] if st.session_state.ai_result['type'] == 'restructured' else st.session_state.ai_result['long_version']
                st.session_state.uploader.copy_to_clipboard(content)
                st.success("클립보드에 복사되었습니다!")
            except Exception as e:
                st.error(f"복사 중 오류가 발생했습니다: {str(e)}")
    
    with col2:
        save_platform = st.selectbox(
            "저장할 플랫폼 선택",
            options=["옵시디언", "노션"],
            key="save_platform"
        )
        
        if st.button("💾 선택한 플랫폼에 저장", use_container_width=True):
            try:
                with st.spinner(f"{save_platform}에 저장 중..."):
                    if save_platform == "옵시디언":
                        result = st.session_state.uploader.save_to_obsidian(st.session_state.ai_result)
                    else:  # 노션
                        result = st.session_state.uploader.save_to_notion(st.session_state.ai_result)
                    
                    if result['status'] == 'success':
                        st.success(result['message'])
                        if save_platform == "옵시디언":
                            st.info(f"저장 위치: {result['path']}")
                        else:
                            st.info("노션에서 확인하세요.")
                    else:
                        st.error("저장에 실패했습니다.")
                        
            except Exception as e:
                st.error(f"저장 중 오류가 발생했습니다: {str(e)}")
                if "API" in str(e):
                    st.info(f"{save_platform} API 설정을 확인해주세요.")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        Made with ❤️ by Your Team | 
        <a href='https://github.com/your-repo'>GitHub</a>
    </div>
    """,
    unsafe_allow_html=True
) 