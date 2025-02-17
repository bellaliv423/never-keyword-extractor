import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
import random
from dotenv import load_dotenv
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from concurrent.futures import ThreadPoolExecutor
import threading
from functools import lru_cache
import logging
from datetime import datetime, timedelta
import platform
import shutil
import re

class NaverCrawlerException(Exception):
    """네이버 크롤러 관련 커스텀 예외"""
    pass

class APIKeyError(NaverCrawlerException):
    """API 키 관련 예외"""
    pass

class ConnectionError(NaverCrawlerException):
    """연결 관련 예외"""
    pass

class NaverCrawler:
    def __init__(self):
        load_dotenv()
        self.setup_logging()
        
        try:
            # API 키 검증
            self.client_id = os.getenv('NAVER_CLIENT_ID')
            self.client_secret = os.getenv('NAVER_CLIENT_SECRET')
            if not self.client_id or not self.client_secret:
                raise Exception("네이버 API 키가 설정되지 않았습니다.")
            
            # 세션 설정
            self.setup_session()
            
            # 상태 초기화    
            self.last_request_time = {}
            self.request_counts = {}
            self.lock = threading.Lock()
            self.cache = {}
            self.cache_timeout = {}
            
            # 웹드라이버는 필요할 때 초기화
            self.driver = None
            
            self.logger.info("네이버 크롤러 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"초기화 중 오류 발생: {str(e)}")
            raise

    def setup_logging(self):
        """로깅 설정"""
        try:
            # 현재 작업 디렉토리 기준으로 로그 경로 설정
            log_path = os.path.join(os.getcwd(), 'logs')
            if not os.path.exists(log_path):
                os.makedirs(log_path)
            
            log_file = os.path.join(log_path, 'crawler.log')
            
            # 로깅 설정
            self.logger = logging.getLogger('NaverCrawler')
            self.logger.setLevel(logging.INFO)
            
            # 파일 핸들러 추가
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # 포맷터 설정
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            # 핸들러 추가
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            print(f"로깅 설정 중 오류 발생: {str(e)}")
            raise

    def setup_chrome_driver(self):
        """크롬 드라이버 설정"""
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920x1080')
            
            # ChromeDriver 자동 설치 및 설정
            service = Service(ChromeDriverManager().install())
            
            # Chrome 브라우저 실행
            self.driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
            
            self.driver.set_page_load_timeout(30)
            self.logger.info("크롬 드라이버 설정 완료")
            
        except Exception as e:
            self.logger.error(f"크롬 드라이버 설정 중 오류 발생: {str(e)}")
            # 웹드라이버 없이도 작동할 수 있도록 설정
            self.driver = None

    def setup_session(self):
        """세션 설정"""
        try:
            self.session = requests.Session()
            self.headers = {
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            self.session.headers.update(self.headers)
            
            # 세션 연결 테스트
            self.test_connection()
            
            self.logger.info("네이버 API 세션 설정 완료")
            
        except Exception as e:
            self.logger.error(f"세션 설정 중 오류 발생: {str(e)}")
            raise ConnectionError(f"네이버 API 연결 테스트 실패: {str(e)}")

    def test_connection(self):
        url = "https://openapi.naver.com/v1/search/news.json"
        params = {"query": "test", "display": 1}
        
        response = requests.get(
            url,
            headers=self.headers,
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"네이버 API 연결 테스트 실패: {response.status_code} {response.text}")

    def get_dynamic_delay(self, endpoint):
        """동적 딜레이 계산"""
        with self.lock:
            current_time = datetime.now()
            last_time = self.last_request_time.get(endpoint)
            
            if last_time:
                # 마지막 요청으로부터 경과 시간 계산
                time_diff = (current_time - last_time).total_seconds()
                
                # 요청 빈도에 따른 딜레이 조정
                count = self.request_counts.get(endpoint, 0)
                if count > 10:  # 10회 이상 요청 시
                    delay = random.uniform(2.0, 4.0)
                elif count > 5:  # 5회 이상 요청 시
                    delay = random.uniform(1.0, 2.0)
                else:
                    delay = random.uniform(0.5, 1.0)
                
                # 필요한 경우 추가 대기
                if time_diff < delay:
                    time.sleep(delay - time_diff)
            
            # 카운터 업데이트
            self.last_request_time[endpoint] = current_time
            self.request_counts[endpoint] = self.request_counts.get(endpoint, 0) + 1

    @lru_cache(maxsize=100)
    def get_cached_content(self, url, timeout=3600):
        """캐시된 콘텐츠 반환"""
        return self.session.get(url).text

    def parallel_fetch(self, urls, fetch_function):
        """병렬 처리로 여러 URL 처리"""
        with ThreadPoolExecutor(max_workers=5) as executor:
            return list(executor.map(fetch_function, urls))

    def check_hot_topic(self, title, content=""):
        """제목과 내용을 분석하여 핫토픽/이슈 여부를 판단합니다."""
        # 핫토픽 키워드 카테고리별 분류
        breaking_news = ['단독', '속보', '긴급', '특종', '최초공개', '1보']
        trending = ['화제', '논란', '충격', '파격', '돌발', '이슈']
        viral = ['실시간', '핫이슈', '급상승', '화제성', '관심집중']
        significant = ['중대발표', '특별', '공식', '전격', '전원', '중요']
        
        # 키워드 가중치 설정
        keyword_weights = {
            'breaking_news': 2.0,  # 속보성 뉴스 가중치
            'trending': 1.5,       # 트렌딩 이슈 가중치
            'viral': 1.3,          # 바이럴 콘텐츠 가중치
            'significant': 1.2     # 중요 뉴스 가중치
        }
        
        # 점수 계산
        score = 0
        text = f"{title} {content}".lower()
        
        # 카테고리별 키워드 체크 및 점수 계산
        if any(keyword in text for keyword in breaking_news):
            score += keyword_weights['breaking_news']
        if any(keyword in text for keyword in trending):
            score += keyword_weights['trending']
        if any(keyword in text for keyword in viral):
            score += keyword_weights['viral']
        if any(keyword in text for keyword in significant):
            score += keyword_weights['significant']
            
        # 추가 지표 체크
        if '!' in title or '?' in title:  # 감탄사나 의문문 포함
            score += 0.3
        if '[단독]' in title or '[속보]' in title:  # 특수 태그 포함
            score += 0.5
            
        return score >= 1.5  # 임계값 이상이면 핫토픽으로 판단

    def retry_on_failure(self, func, *args, max_retries=3, delay=1):
        """에러 발생 시 재시도 로직"""
        for attempt in range(max_retries):
            try:
                return func(*args)
            except Exception as e:
                if attempt == max_retries - 1:  # 마지막 시도였을 경우
                    self.logger.error(f"최대 재시도 횟수 초과: {str(e)}")
                    raise
                self.logger.warning(f"재시도 {attempt + 1}/{max_retries}: {str(e)}")
                time.sleep(delay * (attempt + 1))  # 지수 백오프

    def get_blog_contents(self, keyword, count=5):
        """블로그 콘텐츠를 검색합니다."""
        try:
            self.get_dynamic_delay('blog_search')
            url = "https://openapi.naver.com/v1/search/blog.json"
            params = {
                "query": keyword,
                "display": count * 2,  # 더 많은 결과를 가져와서 필터링
                "sort": "date"
            }
            
            response = self.session.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            items = response.json().get('items', [])
            
            # 키워드 관련성 체크 및 필터링
            filtered_items = []
            for item in items:
                # HTML 태그 제거
                title = re.sub('<[^<]+?>', '', item['title'])
                description = re.sub('<[^<]+?>', '', item['description'])
                
                # 제목이나 설명에 키워드가 포함된 경우만 선택
                if keyword.lower() in title.lower() or keyword.lower() in description.lower():
                    is_hot = self.check_hot_topic(title, description)
                    filtered_items.append({
                        "title": title,
                        "link": item['link'],
                        "description": description,
                        "tags": ['#핫토픽', '#트렌드'] if is_hot else []
                    })
                
                if len(filtered_items) >= count:
                    break
            
            return filtered_items[:count]
            
        except Exception as e:
            self.logger.error(f"블로그 검색 중 오류 발생: {str(e)}")
            return []

    def make_request(self, url, params=None, method='GET', retry_count=3):
        """API 요청 공통 함수"""
        for attempt in range(retry_count):
            try:
                # 동적 딜레이 적용
                self.get_dynamic_delay(url)
                
                # 요청 실행
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    timeout=10
                )
                
                # 응답 검증
                response.raise_for_status()
                
                # 응답 파싱
                data = response.json()
                
                # 에러 코드 확인
                if 'errorCode' in data:
                    error_message = data.get('errorMessage', '알 수 없는 오류')
                    if data['errorCode'] in ['024', '025']:  # API 키 관련 오류
                        raise APIKeyError(f"API 키 오류: {error_message}")
                    else:
                        raise NaverCrawlerException(f"API 오류: {error_message}")
                
                return data
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"요청 실패 (시도 {attempt + 1}/{retry_count}): {str(e)}")
                if attempt == retry_count - 1:
                    raise ConnectionError(f"네이버 API 연결 실패: {str(e)}")
                time.sleep(2 ** attempt)  # 지수 백오프
                
            except json.JSONDecodeError as e:
                self.logger.error(f"응답 파싱 오류: {str(e)}")
                raise NaverCrawlerException("잘못된 응답 형식")

    def get_news_articles(self, keyword, count=10):
        """뉴스 기사를 검색합니다."""
        try:
            self.logger.info(f"뉴스 검색 시작: 키워드='{keyword}', 요청 개수={count}")
            
            url = "https://openapi.naver.com/v1/search/news.json"
            params = {
                "query": keyword,
                "display": count * 2,
                "sort": "date"
            }
            
            # API 요청 전 로깅
            self.logger.debug(f"API 요청: URL={url}, 파라미터={params}")
            
            data = self.make_request(url, params)
            total = data.get('total', 0)
            items = data.get('items', [])
            
            # 응답 결과 로깅
            self.logger.info(f"검색 결과: 총 {total}개 중 {len(items)}개 수신")
            
            # 결과 필터링 및 가공
            filtered_items = []
            for idx, item in enumerate(items):
                try:
                    # HTML 태그 제거
                    title = re.sub('<[^<]+?>', '', item['title'])
                    description = re.sub('<[^<]+?>', '', item['description'])
                    
                    # 키워드 관련성 체크
                    if keyword.lower() in title.lower() or keyword.lower() in description.lower():
                        is_hot = self.check_hot_topic(title, description)
                        filtered_items.append({
                            "title": title,
                            "link": item['link'],
                            "description": description,
                            "tags": ['#핫토픽', '#핫이슈'] if is_hot else []
                        })
                        self.logger.debug(f"기사 {idx+1} 처리 완료: {title[:30]}...")
                        
                        if len(filtered_items) >= count:
                            break
                            
                except Exception as e:
                    self.logger.warning(f"항목 처리 중 오류: {str(e)}")
                    continue
            
            self.logger.info(f"최종 필터링 결과: {len(filtered_items)}개의 기사 선택")
            return filtered_items
            
        except APIKeyError:
            self.logger.error("API 키 오류 발생")
            raise
        except Exception as e:
            self.logger.error(f"뉴스 검색 중 오류 발생: {str(e)}")
            return []

    def get_hot_contents(self, keyword, count=15):
        url = f"https://search.naver.com/search.naver?where=view&query={keyword}"
        self.driver.get(url)
        contents = []
        
        try:
            content_items = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.bx"))
            )
            
            for item in content_items[:count]:
                title = item.find_element(By.CSS_SELECTOR, "a.title_link").text
                link = item.find_element(By.CSS_SELECTOR, "a.title_link").get_attribute("href")
                contents.append({"title": title, "link": link})
                
        except Exception as e:
            print(f"핫탄 콘텐츠 수집 중 오류 발생: {str(e)}")
            
        return contents
    
    def get_related_keywords(self, keyword):
        """연관 검색어를 가져옵니다."""
        try:
            self.get_dynamic_delay('related_keywords')
            url = "https://ac.search.naver.com/nx/ac"
            params = {
                "q": keyword,
                "q_enc": "UTF-8",
                "st": "100",
                "frm": "nv",
                "r_format": "json",
                "r_enc": "UTF-8",
                "r_unicode": "0",
                "t_koreng": "1",
                "ans": "2"
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data and 'items' in data and data['items']:
                keywords = [item[0] for item in data['items'][0]][:10]
                return [f"#{k}" for k in keywords]  # 해시태그 형식으로 반환
            return []
            
        except Exception as e:
            self.logger.error(f"연관 검색어 조회 중 오류 발생: {str(e)}")
            return []

    def clear_expired_cache(self):
        """만료된 캐시 정리"""
        current_time = time.time()
        expired_keys = [
            key for key, timeout in self.cache_timeout.items()
            if current_time > timeout
        ]
        for key in expired_keys:
            self.cache.pop(key, None)
            self.cache_timeout.pop(key, None)

    def cache_result(self, key, value, timeout=3600):
        """결과 캐싱"""
        self.clear_expired_cache()  # 만료된 캐시 정리
        self.cache[key] = value
        self.cache_timeout[key] = time.time() + timeout

    def get_cached_result(self, key):
        """캐시된 결과 조회"""
        if key in self.cache and time.time() <= self.cache_timeout.get(key, 0):
            return self.cache[key]
        return None

    def get_trending_keywords(self):
        """실시간 검색어 순위를 가져옵니다."""
        cache_key = 'trending_keywords'
        cached_result = self.get_cached_result(cache_key)
        if cached_result:
            return cached_result

        self.get_dynamic_delay('trending')
        try:
            self.driver.get("https://datalab.naver.com/keyword/realtimeList.naver")
            
            keywords = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.item_title"))
            )
            
            result = [keyword.text for keyword in keywords[:5]]
            self.cache_result(cache_key, result, timeout=300)  # 5분간 캐시
            return result
            
        except Exception as e:
            self.logger.error(f"실시간 검색어 조회 중 오류 발생: {str(e)}")
            return []

    def get_content_from_url(self, url):
        """URL에서 본문 내용을 추출합니다."""
        self.get_dynamic_delay('content_fetch')
        try:
            # 캐시된 콘텐츠 확인
            cached_content = self.get_cached_content(url)
            if cached_content:
                return self._extract_content_from_html(cached_content)
            
            self.driver.get(url)
            time.sleep(1)  # 최소 대기 시간
            
            if "news.naver.com" in url:
                try:
                    article = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#dic_area"))
                    )
                    return article.text.strip()
                except:
                    try:
                        article = self.driver.find_element(By.CSS_SELECTOR, "#articeBody")
                        return article.text.strip()
                    except:
                        return "콘텐츠를 찾을 수 없습니다."
            elif "blog.naver.com" in url:
                try:
                    # iframe으로 전환
                    iframe = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#mainFrame"))
                    )
                    self.driver.switch_to.frame(iframe)
                    
                    # 본문 추출
                    article = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.se-main-container"))
                    )
                    content = article.text.strip()
                    
                    # 기본 프레임으로 복귀
                    self.driver.switch_to.default_content()
                    return content
                except:
                    try:
                        # 구버전 블로그 형식
                        article = self.driver.find_element(By.CSS_SELECTOR, "div.post-view")
                        return article.text.strip()
                    except:
                        return "콘텐츠를 찾을 수 없습니다."
            else:
                return "지원하지 않는 URL입니다."
                
        except Exception as e:
            self.logger.error(f"콘텐츠 추출 중 오류 발생: {str(e)}")
            return "콘텐츠를 찾을 수 없습니다."

    def _extract_content_from_html(self, html_content):
        """HTML에서 본문 내용을 추출합니다."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 네이버 뉴스 본문 추출 시도
        article = soup.select_one('#dic_area') or soup.select_one('#articeBody')
        if article:
            return article.get_text().strip()
            
        # 네이버 블로그 본문 추출 시도
        article = soup.select_one('div.se-main-container') or soup.select_one('div.post-view')
        if article:
            return article.get_text().strip()
        
        return "콘텐츠를 찾을 수 없습니다."

    def search_news(self, keyword, display=15):
        """네이버 뉴스 검색 API를 사용하여 뉴스를 검색합니다."""
        try:
            url = "https://openapi.naver.com/v1/search/news.json"
            params = {
                "query": keyword,
                "display": 30,  # 더 많은 결과를 가져와서 필터링
                "sort": "date"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            items = response.json().get('items', [])
            
            # 키워드 관련성 체크 및 필터링
            filtered_items = []
            for item in items:
                # 제목이나 설명에 키워드가 포함된 경우만 선택
                if keyword.lower() in item['title'].lower() or keyword.lower() in item['description'].lower():
                    is_hot = self.check_hot_topic(item['title'], item['description'])
                    item['tags'] = ['#핫토픽', '#핫이슈'] if is_hot else []
                    filtered_items.append(item)
                
                if len(filtered_items) >= display:
                    break
            
            return filtered_items[:display]
            
        except Exception as e:
            print(f"뉴스 검색 중 오류 발생: {str(e)}")
            return []

    def get_random_content(self, keyword, count=5):
        """키워드로 랜덤하게 뉴스나 블로그 콘텐츠를 가져옵니다."""
        self.get_dynamic_delay('random_content')
        contents = []
        try:
            # 병렬로 뉴스와 블로그 콘텐츠 가져오기
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_news = executor.submit(self.search_news, keyword, 10)
                future_blogs = executor.submit(self.get_blog_contents, keyword, 10)
                
                news = future_news.result()
                blogs = future_blogs.result()
            
            # 모든 콘텐츠 합치기
            all_contents = news + blogs
            
            # 랜덤하게 선택
            if all_contents:
                selected = random.sample(all_contents, min(count, len(all_contents)))
                contents.extend(selected)
            
        except Exception as e:
            self.logger.error(f"랜덤 콘텐츠 추출 중 오류 발생: {str(e)}")
        
        return contents

    def get_weekly_trends(self):
        """네이버 데이터랩에서 주간 트렌드를 가져옵니다."""
        try:
            self.driver.get("https://datalab.naver.com/keyword/trendSearch.naver")
            time.sleep(2)
            
            trends = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.rank_inner li.list"))
            )
            
            trend_list = []
            for trend in trends[:5]:  # 상위 5개만 가져오기
                keyword = trend.find_element(By.CSS_SELECTOR, "span.title").text
                trend_list.append(keyword)
            
            return trend_list
            
        except Exception as e:
            print(f"주간 트렌드 조회 중 오류 발생: {str(e)}")
            return ["AI", "ChatGPT", "인공지능", "빅데이터", "메타버스"]  # 기본 트렌드 키워드

    def optimize_request(self, url, params=None):
        """요청 최적화"""
        headers = self.session.headers.copy()
        headers.update({
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        try:
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=10,
                verify=True
            )
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            self.logger.error("요청 시간 초과")
            raise
        except requests.exceptions.RequestException as e:
            self.logger.error(f"요청 중 오류 발생: {str(e)}")
            raise

    def __del__(self):
        """리소스 정리"""
        try:
            self.driver.quit()
            self.session.close()
        except:
            pass 