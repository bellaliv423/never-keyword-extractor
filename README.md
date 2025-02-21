# 네이버 키워드 콘텐츠 추출기

## 소개
네이버 뉴스와 블로그에서 키워드 기반 콘텐츠를 자동으로 수집하고 AI로 가공하는 도구입니다.

## 주요 기능
- 키워드 기반 뉴스/블로그 콘텐츠 자동 추출
- 연관 키워드 추천 및 트렌드 분석
- AI 기반 콘텐츠 요약/재구성 (1000자/450자 버전)
- 옵시디언/노션 자동 연동

## 로컬 실행 방법
1. 레포지토리 클론
```bash
git clone https://github.com/bellaliv423/never-keyword-extractor.git
cd never-keyword-extractor
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 패키지 설치
```bash
pip install -r requirements.txt
```

4. 환경변수 설정
- .env 파일에 네이버 API와 OpenAI API 키 설정 필요
- 자세한 설정 방법은 PROJECT_GUIDE.md 참조

5. 실행
```bash
streamlit run app.py
```

## 라이선스
MIT License
