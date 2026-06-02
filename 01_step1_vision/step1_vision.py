#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEP 1: Google Cloud Vision OCR
식민지 시대 문화유산 기록물을 Vision API로 1차 텍스트 추출

사용법:
    python step1_vision.py \
        --input-dir ./images \
        --output-dir ./vision_results \
        --language-hints ja zh-Hant
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, Any

from google.cloud import vision
from google.protobuf import json_format


def setup_vision_client(key_path: str) -> vision.ImageAnnotatorClient:
    """Vision API 클라이언트 초기화."""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_path
    return vision.ImageAnnotatorClient()


def extract_text_from_image(
    client: vision.ImageAnnotatorClient,
    img_path: Path,
    language_hints: list = None
) -> Tuple[str, Dict]:
    """
    이미지 한 장을 Vision API로 처리.
    
    Returns:
        (평탄 텍스트, 구조 dict)
    """
    if language_hints is None:
        language_hints = ['ja', 'zh-Hant']
    
    with open(img_path, 'rb') as f:
        content = f.read()
    
    image = vision.Image(content=content)
    image_context = vision.ImageContext(language_hints=language_hints)
    
    response = client.document_text_detection(
        image=image,
        image_context=image_context,
    )
    
    if response.error.message:
        raise Exception(f"Vision API 오류: {response.error.message}")
    
    if response.full_text_annotation:
        text = response.full_text_annotation.text.strip()
        full = json_format.MessageToDict(response.full_text_annotation._pb)
        return text, full
    
    return "", {}


def process_images(
    input_dir: Path,
    output_dir: Path,
    key_path: str,
    language_hints: list = None
) -> Dict[str, int]:
    """
    폴더 내 모든 이미지를 일괄 처리.
    
    Returns:
        {'processed': int, 'skipped': int, 'errors': int}
    """
    if language_hints is None:
        language_hints = ['ja', 'zh-Hant']
    
    # Vision 클라이언트 초기화
    client = setup_vision_client(key_path)
    print(f"✔ Vision API 인증 완료")
    print(f"  키 파일: {key_path}")
    
    # 입출력 폴더 검증
    if not input_dir.exists():
        raise RuntimeError(f"입력 폴더 없음: {input_dir}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"  입력: {input_dir}")
    print(f"  출력: {output_dir}")
    
    # 이미지 수집
    valid_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}
    image_paths = sorted([
        p for p in input_dir.rglob('*')
        if p.suffix.lower() in valid_extensions
    ])
    
    print(f"\n처리 대상: 총 {len(image_paths)}장")
    if not image_paths:
        print("⚠️ 이미지가 없습니다.")
        return {'processed': 0, 'skipped': 0, 'errors': 0}
    
    print("처음 3장:")
    for p in image_paths[:3]:
        print(f"  {p.relative_to(input_dir)}")
    
    # 일괄 처리
    processed = skipped = errors = 0
    
    for idx, img_path in enumerate(image_paths, 1):
        rel_path = img_path.relative_to(input_dir)
        out_folder = output_dir / rel_path.parent
        out_folder.mkdir(parents=True, exist_ok=True)
        
        base = img_path.stem
        json_path = out_folder / f"{base}.json"
        err_path = out_folder / f"{base}.err.json"
        txt_path = out_folder / f"{base}.txt"
        
        # 멱등성: 정상 JSON 있으면 스킵
        if json_path.exists():
            skipped += 1
            continue
        
        print(f"[{idx}/{len(image_paths)}] {rel_path}", flush=True)
        
        try:
            text, full = extract_text_from_image(client, img_path, language_hints)
            
            result = {
                "file_path": str(rel_path),
                "vision_raw": text,
                "vision_full": full,
                "processed_at": datetime.now().isoformat(timespec='seconds'),
                "gemini_corrected": ""
            }
            
            json_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            
            # 과거 에러 정리
            if err_path.exists():
                err_path.unlink()
            
            if text:
                txt_path.write_text(text, encoding='utf-8')
                print(f"   -> {len(text)}자 추출")
            else:
                print(f"   -> 텍스트 없음 (도면/사진/공백)")
            
            processed += 1
        
        except Exception as e:
            err = {
                "file_path": str(rel_path),
                "error": str(e),
                "failed_at": datetime.now().isoformat(timespec='seconds')
            }
            err_path.write_text(
                json.dumps(err, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            print(f"   -> 오류: {str(e)[:100]}")
            errors += 1
    
    print(f"\n완료. 처리 {processed} / 스킵 {skipped} / 오류 {errors}")
    
    return {'processed': processed, 'skipped': skipped, 'errors': errors}


def main():
    parser = argparse.ArgumentParser(
        description="STEP 1: Google Cloud Vision OCR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    python step1_vision.py \\
        --input-dir ./images \\
        --output-dir ./vision_results \\
        --key-path /path/to/vision-key.json \\
        --language-hints ja zh-Hant
        """
    )
    
    parser.add_argument(
        '--input-dir',
        type=Path,
        required=True,
        help='원본 이미지 폴더'
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        required=True,
        help='결과 JSON/TXT 저장 폴더 (자동 생성)'
    )
    
    parser.add_argument(
        '--key-path',
        type=str,
        default=os.getenv('VISION_KEY_PATH'),
        help='Vision API 키 파일 경로 (기본값: $VISION_KEY_PATH)'
    )
    
    parser.add_argument(
        '--language-hints',
        nargs='+',
        default=['ja', 'zh-Hant'],
        help='언어 힌트 (기본값: ja zh-Hant)'
    )
    
    args = parser.parse_args()
    
    # 키 경로 검증
    if not args.key_path:
        print("❌ Vision API 키 경로가 필요합니다:")
        print("   1. --key-path 인자로 제공하거나")
        print("   2. VISION_KEY_PATH 환경변수 설정")
        sys.exit(1)
    
    if not Path(args.key_path).exists():
        print(f"❌ 키 파일 없음: {args.key_path}")
        sys.exit(1)
    
    # 처리 실행
    try:
        result = process_images(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            key_path=args.key_path,
            language_hints=args.language_hints
        )
        sys.exit(0 if result['errors'] == 0 else 1)
    
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()