# STEP 1: Google Cloud Vision OCR

본 스크립트는 Google Cloud Vision API를 사용해 식민지 시대 문서 이미지에서 1차 텍스트를 추출합니다.

## 사용법

```bash
python step1_vision.py \
    --input-dir ./images \
    --output-dir ./vision_results \
    --key-path /path/to/vision-key.json \
    --language-hints ja zh-Hant
```

## 요구사항

- Python 3.9+
- Google Cloud Vision API 키 (.json)

## 설치

```bash
pip install -r requirements.txt
```

## 출력

각 이미지마다:
- `{filename}.json` - vision_raw + 메타데이터
- `{filename}.txt` - 평탄 텍스트
- `{filename}.err.json` - (오류 시) 재시도 기록

## 상세 가이드

[환경설정](https://github.com/Song-yiJung/korean-modern-document-ocr/blob/main/docs/환경설정.md) 참조
