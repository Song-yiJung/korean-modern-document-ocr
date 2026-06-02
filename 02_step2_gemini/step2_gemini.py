#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEP 2: Gemini 멀티모달 교정
STEP 1의 vision_raw + 원본 이미지 → Gemini 문맥 기반 교정

사용법:
    python step2_gemini.py \
        --input-dir ./images \
        --result-dir ./vision_results \
        --model models/gemini-2.5-flash
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import google.generativeai as genai
import PIL.Image


# 모델별 가격 정보 (USD per 1M tokens, 2026년 기준)
PRICING_USD_PER_1M = {
    'models/gemini-2.5-flash': {'input': 0.30, 'output': 2.50},
    'models/gemini-2.5-flash-lite': {'input': 0.10, 'output': 0.40},
    'models/gemini-2.5-pro': {'input': 1.25, 'output': 10.00},
}


class CostTracker:
    """호출별 비용 추적."""
    
    def __init__(self, model_name: str, usd_to_krw: int = 1400):
        self.model_name = model_name
        self.usd_to_krw = usd_to_krw
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.cost_usd = 0.0
    
    def add(self, in_tok: int, out_tok: int) -> float:
        """단일 호출 비용 추가."""
        pricing = PRICING_USD_PER_1M.get(self.model_name, {'input': 0.0, 'output': 0.0})
        cost = in_tok * pricing['input'] / 1_000_000 + out_tok * pricing['output'] / 1_000_000
        
        self.calls += 1
        self.input_tokens += in_tok
        self.output_tokens += out_tok
        self.cost_usd += cost
        
        return cost
    
    def summary(self) -> str:
        """누적 비용 요약."""
        if self.calls == 0:
            return "이번 세션에서 새로 처리된 호출이 없습니다 (모두 스킵)."
        
        total_krw = self.cost_usd * self.usd_to_krw
        avg_krw = total_krw / self.calls
        
        return (
            f"본 세션 누적: {self.calls}호출\n"
            f"  입력 토큰:  {self.input_tokens:>10,}\n"
            f"  출력 토큰:  {self.output_tokens:>10,}\n"
            f"  총 비용:    ${self.cost_usd:.4f}  (≈₩{total_krw:,.0f})\n"
            f"  장당 평균:  ≈₩{avg_krw:.1f}"
        )


def load_system_prompt(prompt_file: Path) -> str:
    """외부 파일에서 SYSTEM_PROMPT 로드."""
    if not prompt_file.exists():
        raise FileNotFoundError(f"프롬프트 파일 없음: {prompt_file}")
    return prompt_file.read_text(encoding='utf-8')


def process_documents(
    input_dir: Path,
    result_dir: Path,
    api_key: str,
    model_name: str,
    system_prompt: str,
    sleep_interval: int = 6
) -> Dict[str, int]:
    """
    STEP 1 결과를 읽어 Gemini로 교정.
    
    Returns:
        {'processed': int, 'skipped': int, 'errors': int}
    """
    # Gemini 클라이언트 초기화
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    cost_tracker = CostTracker(model_name)
    
    print(f"✔ Gemini 인증 완료")
    print(f"  모델: {model_name}")
    
    # 입출력 폴더 검증
    if not input_dir.exists():
        raise RuntimeError(f"입력(이미지) 폴더 없음: {input_dir}")
    if not result_dir.exists():
        raise RuntimeError(f"결과(JSON) 폴더 없음: {result_dir}")
    
    print(f"  이미지 폴더: {input_dir}")
    print(f"  결과 폴더: {result_dir}")
    
    # STEP 1 결과 수집
    json_files = sorted([
        f for f in result_dir.rglob('*.json')
        if not f.name.endswith('.err.json')
    ])
    
    print(f"\n교정 대상: 총 {len(json_files)}장")
    if not json_files:
        print("⚠️ JSON 파일이 없습니다.")
        return {'processed': 0, 'skipped': 0, 'errors': 0}
    
    processed = skipped = errors = 0
    
    for i, json_path in enumerate(json_files, 1):
        try:
            data = json.loads(json_path.read_text(encoding='utf-8'))
        except Exception as e:
            print(f"  [SKIP] {json_path.name} — JSON 읽기 실패: {e}")
            continue
        
        file_id = json_path.stem
        txt_path = json_path.with_name(f"{file_id}_gemini_final.txt")
        
        # 멱등성: 이미 교정된 결과 있으면 스킵
        if data.get('gemini_corrected', '').strip():
            skipped += 1
            continue
        
        # vision_raw 추출
        vision_raw = data.get('vision_raw', '')
        rel_file_path = data.get('file_path', '')
        img_path = input_dir / rel_file_path
        
        if not img_path.exists():
            print(f"  [SKIP] {file_id} — 원본 이미지 없음: {img_path}")
            continue
        
        print(f"[{i}/{len(json_files)}] {file_id}", flush=True)
        
        # 프롬프트 구성
        combined_prompt = f"{system_prompt}\n\n[1차 원시 텍스트 (vision_raw)]\n{vision_raw}"
        img = PIL.Image.open(img_path)
        
        try:
            t0 = time.time()
            response = model.generate_content([combined_prompt, img])
            duration = time.time() - t0
            corrected_text = response.text.strip()
            
            # JSON 갱신
            data['gemini_corrected'] = corrected_text
            data['gemini_corrected_at'] = datetime.now().isoformat(timespec='seconds')
            json_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            
            # TXT 별도 저장
            txt_path.write_text(corrected_text, encoding='utf-8')
            
            # 비용 추적
            usage = getattr(response, 'usage_metadata', None)
            if usage:
                in_tok = getattr(usage, 'prompt_token_count', 0) or 0
                out_tok = getattr(usage, 'candidates_token_count', 0) or 0
                cost = cost_tracker.add(in_tok, out_tok)
                krw = cost * cost_tracker.usd_to_krw
                print(f"   -> {len(corrected_text)}자 | {in_tok}+{out_tok} 토큰 | "
                      f"${cost:.4f} (≈₩{krw:.1f}) | {duration:.1f}s")
            else:
                print(f"   -> {len(corrected_text)}자 | {duration:.1f}s")
            
            processed += 1
            time.sleep(sleep_interval)
        
        except Exception as e:
            msg = str(e)
            if '429' in msg:
                print(f"   -> 할당량 초과(429). 60초 대기...")
                time.sleep(60)
            else:
                print(f"   -> 오류: {msg[:120]}")
            errors += 1
    
    print(f"\n완료. 처리 {processed} / 스킵 {skipped} / 오류 {errors}")
    print("=" * 50)
    print(cost_tracker.summary())
    print("=" * 50)
    
    return {'processed': processed, 'skipped': skipped, 'errors': errors}


def main():
    parser = argparse.ArgumentParser(
        description="STEP 2: Gemini 멀티모달 교정",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    python step2_gemini.py \\
        --input-dir ./images \\
        --result-dir ./vision_results \\
        --model models/gemini-2.5-flash \\
        --sleep 6
        """
    )
    
    parser.add_argument(
        '--input-dir',
        type=Path,
        required=True,
        help='원본 이미지 폴더'
    )
    
    parser.add_argument(
        '--result-dir',
        type=Path,
        required=True,
        help='STEP 1 결과 JSON 저장 폴더'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='models/gemini-2.5-flash',
        choices=list(PRICING_USD_PER_1M.keys()),
        help='Gemini 모델 (기본값: gemini-2.5-flash)'
    )
    
    parser.add_argument(
        '--sleep',
        type=int,
        default=6,
        help='호출 간격(초) — RPM 한도에 맞춤 (기본값: 6)'
    )
    
    parser.add_argument(
        '--prompt-file',
        type=Path,
        default=Path(__file__).parent / 'system_prompt.md',
        help='SYSTEM_PROMPT 파일 (기본값: ./system_prompt.md)'
    )
    
    args = parser.parse_args()
    
    # API 키 검증
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ Gemini API 키가 필요합니다:")
        print("   1. GEMINI_API_KEY 환경변수 설정하거나")
        print("   2. .env 파일에 작성")
        sys.exit(1)
    
    # 프롬프트 로드
    try:
        system_prompt = load_system_prompt(args.prompt_file)
        print(f"✔ SYSTEM_PROMPT 로드 ({len(system_prompt):,}자)")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # 처리 실행
    try:
        result = process_documents(
            input_dir=args.input_dir,
            result_dir=args.result_dir,
            api_key=api_key,
            model_name=args.model,
            system_prompt=system_prompt,
            sleep_interval=args.sleep
        )
        sys.exit(0 if result['errors'] == 0 else 1)
    
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()