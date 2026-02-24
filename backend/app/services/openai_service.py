"""OpenAI API 서비스"""
import os
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# OpenAI 클라이언트 초기화
_client = None


def get_openai_client() -> OpenAI:
    """OpenAI 클라이언트 반환 (싱글톤)"""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        _client = OpenAI(api_key=api_key)
    return _client


def get_model() -> str:
    """사용할 모델명 반환"""
    return os.getenv("OPENAI_MODEL", "gpt-4o")


def get_max_tokens(model: str) -> int:
    """모델별 최대 출력 토큰 반환"""
    # gpt-4o 계열은 16384, 나머지는 4096
    if "gpt-4o" in model:
        return 16000
    return 4096


async def generate_article_content(prompt: str) -> str:
    """
    프롬프트를 기반으로 대출약정서 조항 내용 생성

    Args:
        prompt: 생성 프롬프트

    Returns:
        생성된 조항 내용
    """
    client = get_openai_client()
    model = get_model()
    max_tokens = get_max_tokens(model)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "당신은 대출약정서 작성 전문가입니다. 주어진 지침에 따라 정확하고 법적으로 유효한 대출약정서 조항을 작성합니다."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,  # 일관성 있는 법률 문서 생성을 위해 낮은 temperature
        max_tokens=max_tokens
    )

    return response.choices[0].message.content


def check_api_key_configured() -> bool:
    """API 키가 설정되어 있는지 확인"""
    api_key = os.getenv("OPENAI_API_KEY")
    return api_key is not None and api_key != "" and not api_key.startswith("sk-your")
