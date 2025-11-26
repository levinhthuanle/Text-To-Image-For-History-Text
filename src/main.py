from __future__ import annotations

import argparse
import logging
from dataclasses import replace
from pathlib import Path

from pipeline import DatasetPipeline, PipelineConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dataset generation pipeline")
    parser.add_argument("--raw-dir", type=Path, help="Directory containing input PDF files")
    parser.add_argument("--image-dir", type=Path, help="Directory to store generated page images")
    parser.add_argument("--annotations", type=Path, help="Output JSONL annotations path")
    parser.add_argument("--pattern", type=str, help="Glob pattern to match PDF filenames")
    parser.add_argument("--dpi", type=int, help="Resolution for PDF to image conversion")
    parser.add_argument(
        "--overwrite-images",
        action="store_true",
        help="Regenerate page images even if they already exist",
    )
    parser.add_argument(
        "--convert-only",
        action="store_true",
        help="Only convert PDFs to images and skip OCR/caption steps",
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> PipelineConfig:
    config = PipelineConfig()
    if args.raw_dir:
        config = replace(config, raw_pdf_dir=args.raw_dir)
    if args.image_dir:
        config = replace(config, image_output_dir=args.image_dir)
    if args.annotations:
        config = replace(config, annotation_output_path=args.annotations)
    if args.pattern:
        config = replace(config, pdf_glob_pattern=args.pattern)
    if args.dpi:
        config = replace(config, dpi=args.dpi)
    if args.overwrite_images:
        config = replace(config, overwrite_images=True)

    project_root = Path(__file__).resolve().parent
    return config.resolve(project_root)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()
    config = build_config(args)
    pipeline = DatasetPipeline(config)
    if args.convert_only:
        artifacts = pipeline.convert_pdfs()
        logging.info("Conversion completed: %d base images prepared", len(artifacts))
        return
    pipeline.run()


if __name__ == "__main__":
    main()
