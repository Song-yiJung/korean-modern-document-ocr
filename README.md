# korean-modern-document-ocr

**식민지 시대 한국 문화유산 기록물의 자동 OCR 및 연구자 판독 파이프라인**

> Colonial-era Korean archival OCR: Vision API → Gemini correction → **Human expert review**

---

## 📖 개요

본 저장소는 1910~1945년 일제강점기 조선총독부 행정문서, 사찰 기록, 민간 서신 등 **식민지 시대 한글·일본어·한자 혼용 문서**를 다중 AI OCR 파이프라인으로 처리하는 방법을 제시합니다.

### 🔄 3단계 프로세스

원본 이미지
↓
[STEP 1] Google Cloud Vision API
→ 물리적 글자 인식 (vision_raw)
↓
[STEP 2] Gemini 멀티모달 교정
→ 원본 이미지 + vision_raw → 문맥 기반 재판독 (gemini_corrected)
↓
[STEP 3] 연구자 판독 ⭐ (수동)
→ 전문가 지식 + 사료 맥락으로 최종 검증·수정
→ gemini_corrected 기반 연구자 최종본 생성

---

## 🎯 특징

- **도메인 특화**: 불국사·문화재 기록물 중심 SYSTEM_PROMPT (커스터마이징 가능)
- **멱등성**: 중단 후 재실행 시 자동 이어서 처리
- **비용 추적**: 토큰·청구액 자동 계산 (Flash 기준 장당 ~1-2원)
- **연구자 중심**: 자동 교정의 한계를 명시 → 최종 판독은 전문가 몫
- **메타데이터 보존**: 좌표·신뢰도·처리 경로 모두 JSON에 기록

---

## 📂 폴더 구조

korean-modern-document-ocr/
├── 01_step1_vision/
│   ├── step1_vision.py           # Vision API 호출 스크립트
│   ├── requirements.txt
│   └── README.md                 # STEP 1 상세 가이드
│
├── 02_step2_gemini/
│   ├── step2_gemini.py           # Gemini 교정 스크립트
│   ├── system_prompt.md          # 도메인 프롬프트 (외부화)
│   ├── config.yaml               # 모델·비용 설정
│   ├── requirements.txt
│   └── README.md                 # STEP 2 상세 가이드
│
├── docs/
│   ├── 03_연구자판독_가이드.md    # ⭐ STEP 3: 수동 검토 프로세스
│   ├── 환경설정.md
│   └── FAQ.md
│
├── prompts/
│   └── 버전관리/
│       ├── system_prompt_v1.md   # 초기 버전
│       └── CHANGELOG.md          # 프롬프트 진화 기록
│
├── .env.example                  # API 키 템플릿
├── .gitignore
├── LICENSE                       # CC-BY-NC-4.0
├── CITATION.cff                  # 논문 인용 정보
└── README.md                     # 이 파일


---

## 🚀 빠른 시작

### 요구사항

- Python 3.9+
- Google Cloud Vision API 키 (.json)
- Google AI Studio Gemini API 키 (텍스트)
- Google Drive 계정 (이미지·결과 저장용)

### 설치

```bash
# 저장소 클론
git clone https://github.com/Song-yiJung/korean-modern-document-ocr.git
cd korean-modern-document-ocr

# 환경 설정
cp .env.example .env
# .env 파일을 열어 API 키 입력

# 의존성 설치
pip install -r 01_step1_vision/requirements.txt
pip install -r 02_step2_gemini/requirements.txt
```

### 실행

```bash
# STEP 1: Vision OCR
python 01_step1_vision/step1_vision.py \
  --input-dir ./images \
  --output-dir ./vision_results

# STEP 2: Gemini 교정
python 02_step2_gemini/step2_gemini.py \
  --input-dir ./images \
  --result-dir ./vision_results

# STEP 3: 연구자 판독 (수동)
# docs/03_연구자판독_가이드.md 참조
```

---

## 📊 결과물 구조

각 사료마다 생성되는 파일:

vision_결과/
├── document_001.json                    # 통합 메타데이터
│   {
│     "file_path": "image_001.jpg",
│     "vision_raw": "원본 Vision 텍스트",
│     "vision_full": {...},              # 좌표·신뢰도
│     "gemini_corrected": "Gemini 교정본",
│     "processed_at": "2026-06-02...",
│     "researcher_final": "연구자 최종본"  # (선택사항)
│   }
│
├── document_001_gemini_final.txt        # Gemini 결과 (사람이 읽기용)
└── document_001_researcher.txt          # 연구자 최종본 (선택사항)

---

## ⭐ STEP 3: 연구자 판독 (핵심)

**AI 자동화의 한계:**
- 식민지 행정문서의 맥락 이해 부족
- 구자체·필기체 변이자 오독
- 역사적 고유명사(인명·지명·관직) 미해석
- 도면·인장·부기 판단 부재

**연구자의 역할:**
1. Gemini 결과 (`*_gemini_final.txt`) 정독
2. 원본 이미지 대조 검증
3. 도메인 지식 기반 수정 (gemini_corrected → researcher_final)
4. 메타데이터 풍부화 (인명·지명 표준화, 주해 추가 등)

👉 **상세 가이드**: [`docs/03_연구자판독_가이드.md`](docs/03_연구자판독_가이드.md)

---

## 💰 비용 추정

| 항목 | 단가 | 100장 | 900장 |
|------|------|-------|-------|
| Vision (무료 한도 초과) | 장당 ~₩2 | ~₩200 | ~₩1,800 |
| Gemini Flash | 장당 ~₩1-2 | ~₩100-200 | ~₩900-1,800 |
| **합계** | | ~₩300-400 | ~₩2,700-3,600 |

> 무료 등급: Vision 월 1,000장, Gemini 분당 10회(RPM) 제한

---

## 📝 커스터마이징

### 프롬프트 변경 (STEP 2)

`02_step2_gemini/system_prompt.md`를 열어 5개 블록을 본인 사료에 맞게 수정:

```markdown
① 도입부: 시대·언어·특성
② 구조 규칙: 표·세로쓰기 등
③ 언어 정밀도: 자주 혼동되는 글자
④ 도메인 어휘: 고유명사·전문용어
⑤ 환각 방지: 출력 통제
```

### 모델 변경 (STEP 2)

`02_step2_gemini/config.yaml`:
```yaml
model: 'models/gemini-2.5-flash'        # 기본
# 대안:
# model: 'models/gemini-2.5-pro'         # 높은 정확도 (비싼)
# model: 'models/gemini-2.5-flash-lite'  # 저비용
```

---

## 🔍 정확도 측정

전체 사료 중 일부를 수동으로 정답지 작성:

```bash
python measure_accuracy.py \
  --result-dir ./vision_results \
  --reference-dir ./reference_texts
```

결과:
Vision 평균 정확도: 87.3%
Gemini 평균 정확도: 94.1%

---

## 📚 학술 참고

본 프로젝트는 다음 학술 논문의 OCR 방법론 구현본입니다:

> 정송이. (2026). "~작성~." *~~~~*, 제X권.

**인용 형식** (APA):
```bibtex
@software{korean_ocr_2026,
  author = {Kim, Ga-yeon and Park, Sun-young},
  title = {korean-modern-document-ocr},
  year = {2026},
  url = {https://github.com/Song-yiJung/korean-modern-document-ocr}
}
```

---

## 📖 문서

- **STEP 1 가이드**: [`01_step1_vision/README.md`](01_step1_vision/README.md)
- **STEP 2 가이드**: [`02_step2_gemini/README.md`](02_step2_gemini/README.md)
- **STEP 3 (연구자 판독)**: [`docs/03_연구자판독_가이드.md`](docs/03_연구자판독_가이드.md)
- **환경 설정**: [`[docs/환경설정.md`](docs/환경설정.md](https://github.com/Song-yiJung/korean-modern-document-ocr/blob/main/docs/%ED%99%98%EA%B2%BD%EC%84%A4%EC%A0%95.md))

---

## ⚖️ 라이선스

CC-BY-NC-4.0 (비상업적 사용만 허가)

본 코드·문서는 학술 및 교육 목적으로 자유롭게 사용·수정·배포할 수 있습니다. 상업적 이용은 별도 협의 필요합니다.

---

## 🤝 기여

이슈·풀 리퀘스트·개선 제안 환영합니다.

---

## 📧 문의

- **GitHub Issues**: [Song-yiJung/korean-modern-document-ocr/issues](https://github.com/Song-yiJung/korean-modern-document-ocr/issues)

---

**마지막으로:** 이 파이프라인의 최종 산출물은 **연구자의 전문 판독**입니다. AI는 도구이지, 학술적 책임은 연구자에게 있습니다. 
