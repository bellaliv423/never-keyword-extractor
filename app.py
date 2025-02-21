import streamlit as st

# 반드시 다른 st 명령어보다 먼저 실행되어야 함
st.set_page_config(
    page_title="스마트 키워드 콘텐츠 추출기",
    page_icon="📰",
    layout="wide"
)

# 이후 다른 import문들
import os
from dotenv import load_dotenv

# 환경변수 로딩을 가장 먼저
try:
    # 현재 스크립트 경로 확인
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(current_dir, '.env')
    
    # 환경변수 로드
    load_dotenv(dotenv_path=env_path, override=True)
    
    # 환경변수 값 확인
    naver_client_id = os.getenv('NAVER_CLIENT_ID')
    naver_client_secret = os.getenv('NAVER_CLIENT_SECRET')
    
    # 환경변수가 제대로 로드되었는지 확인
    if not naver_client_id or not naver_client_secret:
        raise Exception("네이버 API 키가 설정되지 않았습니다.")
    
    # 디버깅용 출력 제거
    st.success("환경 변수가 성공적으로 로드되었습니다.")
    
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
    except Exception as e:
        st.error("초기화 중 오류가 발생했습니다.")
        st.error(str(e))
        st.info("설정을 확인해주세요.")
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
            options=["재구성 (1000자)", "요약 (500자)"],
            help="AI가 콘텐츠를 처리하는 방식을 선택합니다."
        )
        
        translation_enabled = st.checkbox(
            "번역 활성화",
            value=False,
            help="처리된 콘텐츠를 다른 언어로 번역합니다."
        )
        
        if translation_enabled:
            target_language = st.selectbox(
                "번역 언어",
                options=[
                    "영어 (en)", 
                    "일본어 (ja)", 
                    "중국어(간체) (zh-CN)",
                    "중국어(번체) (zh-TW)", 
                    "한국어 (ko)"
                ],
                format_func=lambda x: x.split(" (")[0],
                help="번역할 목표 언어를 선택합니다."
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
if 'news_results' in st.session_state or 'blog_results' in st.session_state:
    st.markdown("---")
    st.subheader("🤖 AI 처리 및 번역")
    
    # 콘텐츠 선택 UI
    all_contents = []
    if 'news_results' in st.session_state:
        all_contents.extend([{'type': 'news', **item} for item in st.session_state.news_results])
    if 'blog_results' in st.session_state:
        all_contents.extend([{'type': 'blog', **item} for item in st.session_state.blog_results])
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_title = st.selectbox(
            "처리할 콘텐츠 선택",
            options=[item['title'] for item in all_contents],
            format_func=lambda x: f"[{next(item['type'] for item in all_contents if item['title'] == x)}] {x}"
        )
        
        selected_content = next(item for item in all_contents if item['title'] == selected_title)
    
    with col2:
        if st.button("🔄 처리 시작", use_container_width=True):
            with st.spinner("콘텐츠를 처리하고 있습니다..."):
                try:
                    processor = ContentProcessor()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    add_script_run_ctx()
                    
                    # AI 처리
                    result = loop.run_until_complete(
                        processor.process_content(selected_content, 
                                               mode="재구성" if "재구성" in ai_mode else "요약")
                    )
                    
                    # 번역 처리
                    if translation_enabled:
                        lang_code = target_language.split(" (")[1].rstrip(")")
                        content_to_translate = result['long_version'] if "재구성" in ai_mode else result['short_version']
                        translation_result = loop.run_until_complete(
                            processor.translate_content(content_to_translate, lang_code)
                        )
                        result['translated_text'] = translation_result['translated_text']
                        result['target_language'] = lang_code
                    
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
    
    tabs = ["원문"]
    if translation_enabled:
        tabs.append("번역본")
    
    result_tabs = st.tabs(tabs)
    
    with result_tabs[0]:
        if st.session_state.ai_result['type'] == 'summary':
            st.markdown("### 요약 (500자)")
            st.markdown(st.session_state.ai_result['short_version'])
        else:
            st.markdown("### 재구성 (1000자)")
            st.markdown(st.session_state.ai_result['long_version'])
    
    if translation_enabled and len(result_tabs) > 1:
        with result_tabs[1]:
            st.markdown(f"### 번역본 ({target_language.split(' (')[0]})")
            st.markdown(st.session_state.ai_result.get('translated_text', ''))
    
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
                # 결과 타입에 따라 적절한 내용 선택
                if st.session_state.ai_result['type'] == 'summary':
                    content = st.session_state.ai_result['short_version']
                else:  # restructured
                    content = st.session_state.ai_result['long_version']
                
                # 복사할 내용을 표시
                formatted_content = st.session_state.uploader.copy_to_clipboard(content)
                st.code(formatted_content, language="markdown")
                st.info("위 텍스트를 선택하여 복사해주세요! (Ctrl+A, Ctrl+C)")
            except Exception as e:
                st.error(f"복사 준비 중 오류가 발생했습니다: {str(e)}")
    
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

class APIKeyError(Exception):
    pass 