#!/bin/bash
# Deprecate, trying to use src/convert_image.py instead
# Fast PDF to PNG conversion with parallel processing and progress monitoring

# Output directory
mkdir -p ../dataset/image

# Function to convert a single PDF
convert_pdf() {
    pdf="$1"
    filename=$(basename "$pdf")        # e.g., lich-su-va-dia-li-6.pdf
    base="${filename%.pdf}"            # e.g., lich-su-va-dia-li-6

    echo "[START] $filename"

    # Convert PDF to PNG at 150 DPI
    pdftoppm -png -r 150 "$pdf" "../dataset/image/SGK_${base}_page"

    # Rename pages to match SGK_${base}_page_1.png format
    for f in ../dataset/image/SGK_${base}_page-*.png; do
        new_f="${f/-/_}"
        mv "$f" "$new_f"
    done

    echo "[DONE ] $filename"
}

export -f convert_pdf

# Count total PDFs for progress
total_pdfs=$(find ../raw/ -name "lich-su-va-dia-li-*.pdf" | wc -l)
echo "Total PDFs to convert: $total_pdfs"

# Run all PDFs in parallel (adjust -j based on CPU cores)
find ../raw/ -name "lich-su-va-dia-li-*.pdf" | parallel -j4 --bar convert_pdf {}

echo "All conversions completed. PNG images are in ../dataset/image/"
