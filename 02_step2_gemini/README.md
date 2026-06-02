# STEP 2: Gemini 멀티모달 교정

STEP 1의 vision_raw와 원본 이미지를 Gemini에 보내 문맥 기반 교정을 수행합니다.

## 사용법

```bash
python step2_gemini.py \
    --input-dir ./images \
    --result-dir ./vision_results \
    --model models/gemini-2.5-flash \
    --prompt-file ./system_prompt.md
```

## 요구사항

- Python 3.9+
- Google AI Studio Gemini API 키
- STEP 1 결과 JSON 파일들

## 설치

```bash
pip install -r requirements.txt
```

## 설정

- `system_prompt.md`: 도메인 특화 프롬프트 (본인 사료에 맞게 수정)
- `config.yaml`: 모델 및 비용 설정

## 출력

- JSON의 `gemini_corrected` 필드 업데이트
- `{filename}_gemini_final.txt` - 교정 결과

## 상세 가이드

[STEP 3: 연구자 판독](../../docs/03_연구자판독_가이드.md) 참조