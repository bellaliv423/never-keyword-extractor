# 스마트 키워드 콘텐츠 추출기 프로젝트 가이드

## 1. 프로젝트 개요

이 프로젝트는 네이버의 실시간 콘텐츠를 스마트하게 수집하고 가공하는 도구입니다.

### 주요 기능
1. 키워드 기반 콘텐츠 추출
   - 뉴스 10개, 블로그 콘텐츠 5개 추출
   - 키워드 연관성이 높은 뉴스 선별
   - 핫토픽/이슈 태그 자동 추가

2. 연관 키워드 추천
   - 입력 키워드 기반 연관 검색어 10개 추출
   - 랜덤 선택된 키워드로 추가 콘텐츠 5개 제공

3. 트렌드 분석
   - 네이버 실시간 인기 뉴스 5개 제공
   - 실시간 검색어 TOP 5 및 관련 뉴스

4. AI 기반 콘텐츠 가공
   - OpenAI API 활용 콘텐츠 재구성
   - 1000자/450자 두 가지 버전 제공

5. 콘텐츠 저장 및 연동
   - 옵시디언/노션 연동
   - 클립보드 복사 기능

## 2. 설치 및 설정

### 2.1 필수 요구사항
- Python 3.8 이상
- Chrome 브라우저 (최신 버전)
- pip (패키지 관리자)

### 2.2 설치 과정

1. 프로젝트 클론 또는 다운로드
```bash
git clone [프로젝트_URL]
cd [프로젝트_디렉토리]
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. 필요 패키지 설치
```bash
pip install -r requirements.txt
```

### 2.3 환경변수 설정

`.env` 파일을 프로젝트 루트 디렉토리에 생성하고 다음 내용을 입력:

```env
# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key_here

# 네이버 API 설정
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here

# 노션 API 설정 (선택사항)
NOTION_TOKEN=your_notion_token_here
NOTION_DATABASE_ID=your_notion_database_id_here

# 옵시디언 설정 (선택사항)
OBSIDIAN_VAULT_PATH=your_obsidian_vault_path_here
```

## 3. 실행 방법

1. 가상환경이 활성화되어 있는지 확인

2. Streamlit 앱 실행
```bash
streamlit run app.py
```

3. 웹 브라우저에서 접속
   - 기본 URL: http://localhost:8501

## 4. 주요 모듈 설명

### 4.1 modules/naver_crawler.py
- 네이버 크롤링 담당
- 뉴스, 블로그, 연관 검색어 수집
- 로봇 정책 준수를 위한 딜레이 설정

### 4.2 modules/content_processor.py
- OpenAI API 연동
- 콘텐츠 요약 및 재구성
- 키워드 추출

### 4.3 modules/content_uploader.py
- 옵시디언/노션 연동
- 파일 저장 및 업로드
- 클립보드 복사 기능

## 5. 사용 방법

1. 키워드 검색
   - 검색창에 키워드 입력
   - 뉴스/블로그 개수 설정 (사이드바)
   - "검색 시작" 버튼 클릭

2. AI 처리
   - 검색 결과에서 원하는 콘텐츠 선택
   - AI 처리 모드 선택 (요약/재구성)
   - "AI 처리 시작" 버튼 클릭

3. 결과 저장
   - 처리된 콘텐츠 확인
   - 원하는 저장 플랫폼 선택
   - "선택한 플랫폼에 저장" 버튼 클릭

## 6. 문제 해결

### 6.1 자주 발생하는 오류

1. OpenAI API 오류
```
해결방법:
- API 키 확인
- 버전 호환성 체크: pip install --upgrade openai
- 프록시 설정 확인
```

2. 크롬드라이버 오류
```
해결방법:
- 크롬 브라우저 업데이트
- 크롬드라이버 재설치
- webdriver_manager 업데이트
```

3. 노션/옵시디언 연동 오류
```
해결방법:
- API 토큰 확인
- 권한 설정 확인
- 경로 설정 확인
```

### 6.2 성능 최적화
- 크롤링 딜레이 조정
- 캐시 활용
- 병렬 처리 구현

## 7. 유지보수

### 7.1 로그 확인
- `crawler.log`: 크롤링 관련 로그
- `content_processor.log`: AI 처리 로그
- `uploader.log`: 업로드 관련 로그

### 7.2 정기적인 업데이트
- 패키지 버전 관리
- API 호환성 체크
- 보안 업데이트

## 8. 보안 주의사항

1. API 키 관리
   - .env 파일 사용
   - .gitignore에 포함
   - 정기적인 키 로테이션

2. 크롤링 정책
   - 네이버 로봇 정책 준수
   - 적절한 딜레이 설정
   - 요청 횟수 제한 준수

3. 데이터 보호
   - 민감정보 암호화
   - 임시 파일 관리
   - 접근 권한 설정

## 9. 향후 개선사항

1. 기능 개선
   - 다중 플랫폼 지원 확대
   - AI 모델 다양화
   - 실시간 알림 기능

2. 성능 최적화
   - 비동기 처리 강화
   - 캐싱 시스템 도입
   - 분산 처리 구현

3. UI/UX 개선
   - 반응형 디자인 강화
   - 사용자 커스터마이징
   - 대시보드 기능

## 10. 참고 자료

- [Streamlit 공식 문서](https://docs.streamlit.io/)
- [OpenAI API 문서](https://platform.openai.com/docs/)
- [네이버 검색 API 문서](https://developers.naver.com/docs/search/)
- [Notion API 문서](https://developers.notion.com/)

## 11. 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 LICENSE 파일을 참조하세요. 

# 네이버 API 검색 크롤러 구현 가이드

## 1. 환경 설정

### 1.1 필수 패키지
```requirements.txt
streamlit==1.31.0
openai==1.11.1
requests==2.31.0
python-dotenv==1.0.0
beautifulsoup4==4.12.2
selenium==4.16.0
webdriver-manager==4.0.1
notion-client==2.2.1
pyperclip==1.8.2
markdown==3.5.2
pandas==2.2.0
pymongo==4.6.1
```

### 1.2 환경변수 설정
```env
# .env 파일
NAVER_CLIENT_ID=your_client_id_here
NAVER_CLIENT_SECRET=your_client_secret_here
OPENAI_API_KEY=your_openai_key_here
```

## 2. 네이버 크롤러 구현

### 2.1 기본 구조
```python
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
                raise APIKeyError("네이버 API 키가 설정되지 않았습니다.")
            
            # 세션 설정
            self.setup_session()
            
            # 상태 초기화    
            self.last_request_time = {}
            self.request_counts = {}
            self.lock = threading.Lock()
            self.cache = {}
            self.cache_timeout = {}
            
            self.logger.info("네이버 크롤러 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"초기화 중 오류 발생: {str(e)}")
            raise
```

### 2.2 세션 설정
```python
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
        test_url = "https://openapi.naver.com/v1/search/news.json"
        test_params = {"query": "test", "display": 1}
        response = self.session.get(test_url, params=test_params)
        response.raise_for_status()
        
        self.logger.info("네이버 API 세션 설정 완료")
        
    except Exception as e:
        self.logger.error(f"세션 설정 중 오류 발생: {str(e)}")
        raise ConnectionError(f"네이버 API 연결 테스트 실패: {str(e)}")
```

### 2.3 뉴스 검색 구현
```python
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
                title = re.sub('<[^<]+?>', '', item['title'])
                description = re.sub('<[^<]+?>', '', item['description'])
                
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
```

### 2.4 API 요청 공통 함수
```python
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
```

## 3. 주요 기능

1. API 키 자동 검증
2. 세션 관리 및 연결 테스트
3. 동적 딜레이로 요청 제한 준수
4. 자동 재시도 메커니즘
5. 상세한 로깅
6. 에러 처리 및 복구
7. 결과 필터링 및 가공

## 4. 사용 예시

```python
# 크롤러 초기화
crawler = NaverCrawler()

# 뉴스 검색
news_results = crawler.get_news_articles("AI", count=10)

# 결과 출력
for article in news_results:
    print(f"제목: {article['title']}")
    print(f"링크: {article['link']}")
    print(f"설명: {article['description']}")
    print(f"태그: {article['tags']}")
    print("---")
```

## 5. 주의사항

1. API 키는 반드시 .env 파일에 저장
2. 요청 제한 준수를 위한 동적 딜레이 사용
3. 에러 처리 및 로깅 활성화
4. 재시도 메커니즘 구현
5. 결과 필터링 로직 구현

이 가이드를 참고하여 네이버 API를 활용한 검색 크롤러를 구현할 수 있습니다. 