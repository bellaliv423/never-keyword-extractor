from datetime import datetime
import os
import json
import requests
from dotenv import load_dotenv
from .naver_crawler import NaverCrawler
import random
from typing import Dict, Optional, Union
import logging
import pyperclip
from pathlib import Path
import markdown
import re
from notion_client import Client

class ContentUploaderException(Exception):
    """업로더 관련 커스텀 예외"""
    pass

class ContentUploader:
    def __init__(self):
        self.setup_logging()
        self.setup_notion()
        self.setup_obsidian()
        
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('uploader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_notion(self):
        """노션 설정"""
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        if self.notion_token:
            self.notion = Client(auth=self.notion_token)
        else:
            self.notion = None

    def setup_obsidian(self):
        """옵시디언 설정"""
        self.obsidian_vault = os.getenv('OBSIDIAN_VAULT_PATH')
        if not self.obsidian_vault:
            self.obsidian_vault = os.path.join(os.path.expanduser('~'), 'Documents/Obsidian/Vault')

    def save_to_file(self, content: Dict, platform: str) -> str:
        """콘텐츠를 파일로 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{platform}.txt"
            filepath = self.base_dir / platform / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"콘텐츠 저장 완료: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"파일 저장 중 오류 발생: {str(e)}")
            raise

    def upload_to_obsidian(self, content: Dict) -> Dict:
        """옵시디언에 업로드"""
        try:
            # 마크다운 형식으로 변환
            md_content = self.convert_to_markdown(content)
            
            # 파일 저장
            filepath = self.save_to_file({'markdown': md_content}, 'obsidian')
            
            # 옵시디언 볼트 경로 (환경 변수에서 가져오기)
            vault_path = os.getenv('OBSIDIAN_VAULT_PATH')
            if vault_path:
                target_path = Path(vault_path) / f"네이버_크롤링_{datetime.now().strftime('%Y%m%d')}.md"
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                
                return {
                    "status": "success",
                    "filepath": str(target_path),
                    "message": "옵시디언에 업로드 완료"
                }
            else:
                raise ValueError("옵시디언 볼트 경로가 설정되지 않았습니다.")
            
        except Exception as e:
            self.logger.error(f"옵시디언 업로드 중 오류 발생: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def upload_to_notion(self, content: Dict) -> Dict:
        """노션에 업로드"""
        try:
            notion_token = os.getenv('NOTION_TOKEN')
            notion_database_id = os.getenv('NOTION_DATABASE_ID')
            
            if not notion_token or not notion_database_id:
                raise ValueError("노션 토큰 또는 데이터베이스 ID가 설정되지 않았습니다.")
            
            headers = {
                "Authorization": f"Bearer {notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            # 노션 페이지 생성
            url = f"https://api.notion.com/v1/pages"
            data = {
                "parent": {"database_id": notion_database_id},
                "properties": {
                    "제목": {
                        "title": [
                            {
                                "text": {
                                    "content": content.get("title", "네이버 크롤링 콘텐츠")
                                }
                            }
                        ]
                    }
                },
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": content.get("content", "")
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            return {
                "status": "success",
                "page_id": response.json()["id"],
                "message": "노션에 업로드 완료"
            }
            
        except Exception as e:
            self.logger.error(f"노션 업로드 중 오류 발생: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def copy_to_clipboard(self, content: str) -> bool:
        """클립보드에 복사"""
        try:
            pyperclip.copy(content)
            return True
        except Exception as e:
            self.logger.error(f"클립보드 복사 중 오류: {str(e)}")
            raise ContentUploaderException("클립보드 복사 실패")

    def convert_to_markdown(self, content: Dict) -> str:
        """콘텐츠를 마크다운 형식으로 변환"""
        try:
            md_content = f"""# {content.get('title', '네이버 크롤링 콘텐츠')}

## 원본 콘텐츠
{content.get('original_content', '')}

## 요약본 (1000자)
{content.get('long_version', '')}

## 요약본 (450자)
{content.get('short_version', '')}

## 키워드
{' '.join(content.get('keywords', []))}

---
생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            return md_content
        except Exception as e:
            self.logger.error(f"마크다운 변환 중 오류 발생: {str(e)}")
            return ""

    def save_to_obsidian(self, content: Dict) -> Dict:
        """옵시디언에 저장"""
        try:
            if not os.path.exists(self.obsidian_vault):
                os.makedirs(self.obsidian_vault)
            
            # 파일명 생성
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{self.sanitize_filename(content['title'])}.md"
            filepath = os.path.join(self.obsidian_vault, filename)
            
            # 마크다운 형식으로 변환
            markdown_content = self.format_to_markdown(content)
            
            # 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            return {
                "status": "success",
                "message": "옵시디언에 저장되었습니다",
                "path": filepath
            }
            
        except Exception as e:
            self.logger.error(f"옵시디언 저장 중 오류: {str(e)}")
            raise ContentUploaderException(f"옵시디언 저장 실패: {str(e)}")

    def save_to_notion(self, content: Dict) -> Dict:
        """노션에 저장"""
        try:
            if not self.notion or not self.notion_database_id:
                raise ContentUploaderException("노션 API 설정이 필요합니다")
            
            # 페이지 생성
            page = self.notion.pages.create(
                parent={"database_id": self.notion_database_id},
                properties={
                    "제목": {"title": [{"text": {"content": content['title']}}]},
                    "출처": {"url": content['original_link']},
                    "태그": {"multi_select": [{"name": tag.replace('#', '')} for tag in content.get('keywords', [])]},
                    "작성일": {"date": {"start": datetime.now().isoformat()}}
                },
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": content['content']}}]
                        }
                    }
                ]
            )
            
            return {
                "status": "success",
                "message": "노션에 저장되었습니다",
                "page_id": page.id
            }
            
        except Exception as e:
            self.logger.error(f"노션 저장 중 오류: {str(e)}")
            raise ContentUploaderException(f"노션 저장 실패: {str(e)}")

    def format_to_markdown(self, content: Dict) -> str:
        """마크다운 형식으로 변환"""
        md_template = f"""---
title: {content['title']}
source: {content['original_link']}
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
tags: {' '.join(content.get('keywords', []))}
---

# {content['title']}

## 원문 링크
{content['original_link']}

## 내용
{content['content']}

## 키워드
{' '.join(content.get('keywords', []))}
"""
        return md_template

    def sanitize_filename(self, filename: str) -> str:
        """파일명 정리"""
        # 윈도우 파일명으로 사용할 수 없는 문자 제거
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # 공백을 언더스코어로 변경
        filename = filename.replace(' ', '_')
        # 길이 제한
        return filename[:50]

class KeywordSearcher:
    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv('NAVER_CLIENT_ID')
        self.client_secret = os.getenv('NAVER_CLIENT_SECRET')
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        self.max_retries = 3

    def _make_request(self, url, params=None):
        """API 요청을 수행하고 재시도 로직을 구현합니다."""
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise e
                continue

    def get_related_keywords(self, keyword):
        """연관 키워드를 검색합니다."""
        try:
            url = f"https://ac.search.naver.com/nx/ac"
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
            
            data = self._make_request(url, params)
            if data and 'items' in data and data['items']:
                return [item[0] for item in data['items'][0]][:10]
            return []
            
        except Exception as e:
            print(f"연관 키워드 검색 중 오류 발생: {str(e)}")
            return []

    def search_news(self, keyword):
        """뉴스를 검색합니다."""
        try:
            url = "https://openapi.naver.com/v1/search/news.json"
            params = {
                "query": keyword,
                "display": 15,
                "sort": "date"
            }
            
            data = self._make_request(url, params)
            if data and 'items' in data:
                return data['items']
            return []
            
        except Exception as e:
            print(f"뉴스 검색 중 오류 발생: {str(e)}")
            return []

    def get_popular_keywords(self):
        """실시간 인기 검색어를 가져옵니다."""
        try:
            url = "https://api.signal.bz/news/realtime"
            data = self._make_request(url)
            if data and isinstance(data, list):
                return [item['keyword'] for item in data[:5]]
            return []
            
        except Exception as e:
            print(f"인기 검색어 조회 중 오류 발생: {str(e)}")
            return []

    def get_popular_news(self, keywords):
        """인기 키워드 관련 뉴스를 검색합니다."""
        all_news = []
        for keyword in keywords:
            try:
                news = self.search_news(keyword)[:2]  # 각 키워드당 2개의 뉴스
                all_news.extend(news)
            except Exception as e:
                print(f"인기 뉴스 검색 중 오류 발생 ({keyword}): {str(e)}")
                continue
        return all_news

class ContentExtractor:
    def __init__(self):
        self.crawler = NaverCrawler()

    def extract_contents(self, keyword):
        """키워드 관련 콘텐츠를 추출합니다."""
        try:
            # 뉴스와 블로그 콘텐츠 수집
            news_items = self.crawler.search_news(keyword, display=15)
            blog_items = self.crawler.get_blog_contents(keyword, count=5)
            
            # 연관 키워드 및 랜덤 콘텐츠
            related_keywords = self.crawler.get_related_keywords(keyword)
            random_contents = []
            if related_keywords:
                # 랜덤하게 키워드 선택
                selected_keyword = random.choice(related_keywords)
                random_contents = self.crawler.get_random_content(selected_keyword, count=5)
            
            # 인기 검색어 및 뉴스
            popular_keywords = self.crawler.get_trending_keywords()
            popular_news = []
            for pop_keyword in popular_keywords[:5]:
                news = self.crawler.search_news(pop_keyword, display=2)
                popular_news.extend(news)

            return {
                'news': news_items,
                'blog_contents': blog_items,
                'related_keywords': related_keywords,
                'random_contents': random_contents,
                'popular_keywords': popular_keywords,
                'popular_news': popular_news
            }
        except Exception as e:
            print(f"콘텐츠 추출 중 오류 발생: {str(e)}")
            return {
                'news': [],
                'blog_contents': [],
                'related_keywords': [],
                'random_contents': [],
                'popular_keywords': [],
                'popular_news': []
            } 