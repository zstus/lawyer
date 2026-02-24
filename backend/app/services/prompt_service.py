"""프롬프트 생성 서비스"""
import json


def build_generation_prompt(
    term_sheet_text: str,
    agreement_name: str,
    clause_structure: list
) -> str:
    """대출약정서 조항 생성을 위한 프롬프트 구성

    프롬프트에는 항 정보(항번호, 항제목, 항내용)만 전달합니다.
    조 제목은 프롬프트에 포함하지 않으며, 기준약정서의 조 제목을 그대로 사용합니다.

    Args:
        term_sheet_text: Term Sheet 텍스트
        agreement_name: 참조 약정서 이름
        clause_structure: 참조 항 구조 리스트
            [{"number": "1", "title": "항제목", "content": "항내용"}, ...]

    Returns:
        생성된 프롬프트 문자열
    """
    # 항 구조를 JSON 형식으로 준비
    clause_json_list = []
    for clause in clause_structure:
        clause_json_list.append({
            "clause_number": int(clause['number']) if clause['number'].isdigit() else clause['number'],
            "clause_title": clause['title'],
            "content": clause['content']
        })

    clause_structure_json = json.dumps(clause_json_list, ensure_ascii=False, indent=2)

    prompt = f"""당신은 대출약정서 작성 전문가입니다.

## 목표
- 입력으로 제공되는 **참조 대출약정서 항 JSON 배열의 각 원소를 1:1로 대응**하여,
- **동일한 개수, 동일한 순서, 동일한 clause_number, clause_title**을 유지한 채,
- 각 content에서 **Term Sheet로 인해 바뀌어야 하는 부분만** 대체하여 출력하세요.

## 절대 규칙(강제)
1) **출력 JSON 배열의 길이는 입력 참조 배열의 길이와 반드시 동일**해야 합니다.
   - 예: 참조 배열이 29개면 출력도 **반드시 29개**입니다.
2) **순서 유지**: 입력 배열의 순서를 그대로 유지하세요(정렬/재배치 금지).
3) **키/값 유지**: 각 객체의 `clause_number`, `clause_title`은 입력과 **완전히 동일**해야 하며, `content`만 치환 대상입니다.
4) **문장 구조/형식 최대 유지**
   - 원문 content의 문장, 문단, 항목(번호/기호), 줄바꿈(\\n)을 **그대로 유지**하세요.
   - **새로운 문장/문단/항목을 추가하지 말고**, **삭제하지도 마세요.**
5) **치환 범위 제한(가장 중요)**
   - Term Sheet와 **명확히 대응**되는 값(금액, 날짜, 기간, 비율, 계좌명, 당사자명, 정의, 조건 목록 등)만 해당 문자열을 **치환**하세요.
   - Term Sheet와 무관하거나 대응이 불명확한 문구(일반적으로 사용 가능한 문구 포함)는 **그대로 유지**하여 제시하세요.
6) **Term Sheet에 없는 값 처리**
   - 원문에 존재하는 “구체 값/조건”이 Term Sheet로 치환되어야 하나 Term Sheet에 해당 값이 없으면, **그 값/구문 자리만** 정확히 `[확인 필요]`로 치환하세요.
   - 문장/항 전체를 `[확인 필요]`로 바꾸지 마세요(부분 치환만 허용).
7) **금지사항**
   - 법률 용어/표현 임의 변경 금지
   - 원문에 없는 내용 추가 금지
   - 요약/해설/주석 추가 금지
   - 항의 분리/통합/재구성 금지

---

## Term Sheet 정보

{term_sheet_text}

---

## 참조 대출약정서 항 (원문)

참조 문서: "{agreement_name}"

{clause_structure_json}

---

## 출력 형식

**반드시 아래 JSON 형식으로만 응답하세요. 다른 설명이나 마크다운(##, ** 등)을 사용하지 마세요.**

```json
[
  {{
    "clause_number": 1,
    "clause_title": "항 제목",
    "content": "항 내용 (원문 구조 유지, Term Sheet 값만 대체)"
  }},
  {{
    "clause_number": 2,
    "clause_title": "항 제목",
    "content": "항 내용"
  }}
]
```

---

## 작성 요청

- 위 참조 항들의 문장 구조와 표현을 그대로 유지하면서, Term Sheet의 구체적인 값과 명확히 오버랩되는 부분만 대체하여 JSON 배열로 출력하세요.
- 입력 참조 항 개수와 동일한 개수의 항을 반드시 반환하세요(누락/추가 금지).
- Term Sheet에 없는 정보는 해당 값/구문 자리만 "[확인 필요]"로 표시하세요.
"""

    return prompt
