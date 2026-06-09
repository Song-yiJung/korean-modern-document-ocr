# korean-modern-document-ocr

식민지 시대 한국 기록물 OCR 파이프라인: Vision OCR → Gemini 교정 → 연구자 판독

> 키 발급, Colab 설정, 단계별 실습을 포함한 전체 사용법은 매뉴얼을 참조한다.

> 전체 사용법(키 발급, Colab 설정, 단계별 실습)은 WikiDocs 매뉴얼

> 『근대 사료 1차 가공을 위한 AI 기반 고문서 OCR 매뉴얼』에 정리되어 있다. ([링크 추가 예정](https://wikidocs.net/348351))
---

## 개요

1910–1945년 일제강점기 조선총독부박물관 행정문서, 사찰 기록, 민간 서신 등 일본어·한자 혼용 문서를 OCR로 1차 가공하는 파이프라인이다. 한글은 후대 정리 기록에 일부 나타난다. 자동 처리만으로 완성된 판독본을 만들지 않으며, 최종 판독은 연구자의 검토를 거친다. 모든 코드는 별도의 로컬 환경 설정 없이 Google Colab에서 실행한다.

### 처리 3단계

```
원본 이미지
  ↓
[STEP 1] Google Cloud Vision API   → 글자의 물리적 인식 (vision_raw)
  ↓
[STEP 2] Gemini 멀티모달 교정       → 이미지 + vision_raw로 문맥 기반 재판독 (gemini_corrected)
  ↓
[STEP 3] 연구자 판독 (수동)         → 전문가 지식과 사료 맥락으로 최종 검증·수정 (researcher_final)
```

## 사용법 (Google Colab)
준비물: Google Cloud Vision API 키, Google AI Studio Gemini API 키, Google Drive 계정.

STEP 1 — Vision OCR
1. [Colab에서 step1_vision_colab.ipynb 열기](https://colab.research.google.com/github/Song-yiJung/korean-modern-document-ocr/blob/main/01_step1_vision/step1_vision_colab.ipynb)
2. 사료 이미지를 Google Drive에 업로드하고, Colab Secrets에 Vision API 키를 등록한다.
3. 입력·출력 폴더를 지정하고 셀을 차례로 실행한다.

STEP 2 — Gemini 교정
1. [Colab에서 step2_gemini_colab.ipynb 열기](https://colab.research.google.com/github/Song-yiJung/korean-modern-document-ocr/blob/main/02_step2_gemini/step2_gemini_colab.ipynb)
2. STEP 1 결과 폴더를 입력으로 지정하고, Colab Secrets에 Gemini API 키를 등록한다.
3. 셀을 차례로 실행한다.

STEP 3 — 연구자 판독 (수동)
`docs/03_연구자판독_가이드.md`를 참조한다.

생성되는 결과물은 사료별 통합 메타데이터(JSON)와 사람이 읽기 좋은 교정 텍스트(`*_gemini_final.txt`)이며, 연구자 최종본은 검토 단계에서 추가된다.

## 저장소 구성

```
korean-modern-document-ocr/
├── 01_step1_vision/              # STEP 1: Vision OCR
│   ├── step1_vision_colab.ipynb
│   └── README.md
├── 02_step2_gemini/              # STEP 2: Gemini 교정
│   ├── step2_gemini_colab.ipynb
│   ├── system_prompt.md          #   도메인 프롬프트 (5블록)
│   ├── config.yaml               #   모델·비용 설정
│   └── README.md
├── docs/
│   ├── 03_연구자판독_가이드.md     #   STEP 3 수동 검토 절차
│   ├── 환경설정.md
│   └── FAQ.md
├── .env.example
├── CITATION.cff
├── LICENSE
└── README.md
```

## 연구자 판독 (STEP 3)

이 파이프라인의 최종 산출물은 연구자의 판독본이다. 자동 처리는 식민지 행정문서의 맥락 이해, 구자체·필기체 변이자 판독, 역사적 고유명사 해석, 도면·인장 판단에 한계가 있다. 연구자는 Gemini 결과를 원본 이미지와 대조해 검증·수정하고, 인명·지명 표준화 등 메타데이터를 보강한다.

## 비용
Gemini Flash 기준 장당 약 ₩1–2이며, Vision은 월 1,000장까지 무료이다. (~2026년 5월 기준)

## 커스터마이징

프롬프트: `02_step2_gemini/system_prompt.md`의 다섯 블록(① 도입부 ② 구조 규칙 ③ 언어 정밀도 ④ 도메인 어휘 ⑤ 환각 방지)을 본인 사료에 맞게 수정한다.

모델: `02_step2_gemini/config.yaml`에서 변경한다.

```yaml
model: 'models/gemini-2.5-flash'        # 기본
# model: 'models/gemini-2.5-pro'        # 정확도 높음, 비용 높음
# model: 'models/gemini-2.5-flash-lite' # 저비용
```

## 인용

본 프로젝트는 다음 논문의 OCR 방법론 구현본이다.

> (서지정보 작성 예정)

```bibtex
@software{korean_ocr_2026,
  author = {Jung, Song-yi},
  title  = {korean-modern-document-ocr},
  year   = {2026},
  url    = {https://github.com/Song-yiJung/korean-modern-document-ocr}
}
```

## 라이선스

CC-BY-NC-4.0 (비상업적 사용). 학술·교육 목적의 사용·수정·배포는 자유이며, 상업적 이용은 별도 협의가 필요하다.

## 기여 및 문의

이슈, 풀 리퀘스트, 개선 제안을 환영합니다. 문의는 [GitHub Issues](https://github.com/Song-yiJung/korean-modern-document-ocr/issues)로 받는다.

---

이 파이프라인의 최종 산출물은 연구자의 전문 판독이다. AI는 도구이며, 학술적 책임은 연구자에게 있다.
