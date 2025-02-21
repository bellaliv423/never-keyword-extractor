import os
from openai import AsyncOpenAI
from typing import List, Dict, Optional
from dotenv import load_dotenv
import logging
import json
from datetime import datetime
import openai

class ContentProcessorException(Exception):
    """콘텐츠 처리 관련 커스텀 예외"""
    pass

class ContentProcessor:
    def __init__(self):
        load_dotenv()
        self.setup_logging()
        self.setup_openai()
        
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('content_processor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_openai(self):
        """OpenAI API 설정"""
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
        
        # OpenAI 클라이언트 초기화
        try:
            self.client = AsyncOpenAI(api_key=self.api_key)
        except Exception as e:
            raise ValueError(f"OpenAI 클라이언트 초기화 실패: {str(e)}")

    async def process_content(self, content: Dict, mode: str = 'summarize') -> Dict:
        """콘텐츠 처리 메인 함수"""
        try:
            if not content or 'description' not in content:
                raise ValueError("유효하지 않은 콘텐츠 형식입니다.")

            if mode == '요약':
                # 500자 버전
                summary = await self.summarize_content(content['description'], 500)
                
                return {
                    "type": "summary",
                    "title": content.get('title', ''),
                    "original_link": content.get('link', ''),
                    "short_version": summary['content'],
                    "keywords": await self.extract_keywords(content['description'])
                }
            else:  # 재구성 모드
                restructured = await self.restructure_content(content)
                return {
                    "type": "restructured",
                    "title": content.get('title', ''),
                    "original_link": content.get('link', ''),
                    "long_version": restructured['content'],
                    "keywords": await self.extract_keywords(restructured['content'])
                }
                
        except Exception as e:
            self.logger.error(f"콘텐츠 처리 중 오류 발생: {str(e)}")
            raise ContentProcessorException(f"콘텐츠 처리 실패: {str(e)}")

    async def summarize_content(self, content: str, target_length: int) -> Dict:
        """콘텐츠 요약"""
        try:
            system_prompt = f"""
            다음 내용을 {target_length}자 내외로 요약해주세요.
            요약시 다음 규칙을 따라주세요:
            1. 핵심 내용을 먼저 서술
            2. 중요한 수치나 통계는 유지
            3. 전문 용어는 가능한 쉽게 설명
            4. 문장은 간결하게 구성
            """

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=0.7,
                max_tokens=1500
            )

            summary = response.choices[0].message.content
            return {
                "type": "summary",
                "content": summary,
                "length": len(summary)
            }
            
        except Exception as e:
            self.logger.error(f"요약 중 오류 발생: {str(e)}")
            raise

    async def restructure_content(self, content: Dict) -> Dict:
        """콘텐츠 재구성"""
        try:
            system_prompt = f"""
            다음 내용을 1000자 내외로 재구성해주세요.
            재구성시 다음 규칙을 따라주세요:
            1. 논리적 구조화
            2. 객관적 사실 중심
            3. 핵심 메시지를 강조
            4. 전문 용어는 쉽게 설명
            5. 단락을 적절히 나누어 가독성 향상
            """

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content['description']}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            restructured = response.choices[0].message.content
            return {
                "content": restructured,
                "type": "restructured"
            }
            
        except Exception as e:
            self.logger.error(f"재구성 중 오류 발생: {str(e)}")
            raise

    async def extract_keywords(self, content: str) -> List[str]:
        """주요 키워드 추출"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "다음 내용에서 주요 키워드를 추출하여 해시태그 형식으로 반환해주세요. (최대 10개)"},
                    {"role": "user", "content": content}
                ],
                temperature=0.5,
                max_tokens=200
            )
            
            keywords = response.choices[0].message.content.split()
            return [k for k in keywords if k.startswith('#')]
            
        except Exception as e:
            self.logger.error(f"키워드 추출 중 오류 발생: {str(e)}")
            return []

    async def translate_content(self, content: str, target_lang: str = 'en') -> Dict:
        """콘텐츠 번역"""
        try:
            lang_codes = {
                'en': '영어',
                'ja': '일본어',
                'zh-CN': '중국어(간체)',
                'zh-TW': '중국어(번체)',
                'ko': '한국어'
            }
            
            # 중국어 번역을 위한 특별 프롬프트 추가
            if target_lang.startswith('zh'):
                system_prompt = f"""
                다음 내용을 {lang_codes.get(target_lang, target_lang)}로 번역해주세요.
                번역시 다음 규칙을 따라주세요:
                1. 자연스러운 표현 사용
                2. 전문 용어는 정확하게 번역
                3. 문맥을 고려한 번역
                4. 원문의 뉘앙스 유지
                5. {'번체자를 사용해주세요.' if target_lang == 'zh-TW' else '간체자를 사용해주세요.'}
                """
            else:
                system_prompt = f"""
                다음 내용을 {lang_codes.get(target_lang, target_lang)}로 번역해주세요.
                번역시 다음 규칙을 따라주세요:
                1. 자연스러운 표현 사용
                2. 전문 용어는 정확하게 번역
                3. 문맥을 고려한 번역
                4. 원문의 뉘앙스 유지
                """

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            translated = response.choices[0].message.content
            return {
                "translated_text": translated,
                "source_text": content,
                "target_language": target_lang
            }
            
        except Exception as e:
            self.logger.error(f"번역 중 오류 발생: {str(e)}")
            raise ContentProcessorException(f"번역 실패: {str(e)}") 