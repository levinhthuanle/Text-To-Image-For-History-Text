## Prequisites
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## How to run 
1. Install the dependency: `uv sync`
2. Run full pipeline: `uv run main.py`
	- Optional filters: `--pattern 'lich-su-va-dia-li-*.pdf'`, `--raw-dir PATH`, `--image-dir PATH`, `--annotations PATH`
	- Optional limits: `--limit-pdfs N`, `--limit-pages N`
	- Parallelism: `--num-workers K` to parallelize OCR/caption (default 1)
	- Quality tweak: `--dpi 300` for sharper OCR; add `--overwrite-images` to regenerate PNGs
3. Convert only (skip OCR/caption/QA): `uv run main.py --convert-only [same flags above]`
4. Outputs: images in `dataset/image/`, annotations in `dataset/annotations.jsonl`
