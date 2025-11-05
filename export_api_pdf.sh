#!/bin/bash
# Export API.md to PDF for external sharing
# Requires: pandoc and wkhtmltopdf
# Install: brew install pandoc wkhtmltopdf (macOS) or apt-get install pandoc wkhtmltopdf (Linux)

echo "📄 Exporting API.md to PDF..."

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "❌ pandoc not found. Install with:"
    echo "   macOS: brew install pandoc"
    echo "   Linux: apt-get install pandoc"
    exit 1
fi

# Create PDF with pandoc
pandoc drive-bq-indexer/API.md \
    -o API_OVERVIEW.pdf \
    --pdf-engine=wkhtmltopdf \
    --metadata title="Energy Jibber Jabber API Overview" \
    --metadata author="GB Power Market Team" \
    --metadata date="$(date +%Y-%m-%d)" \
    --toc \
    --toc-depth=2 \
    -V geometry:margin=1in \
    -V fontsize=11pt

if [ $? -eq 0 ]; then
    echo "✅ PDF created: API_OVERVIEW.pdf"
    echo "📊 Size: $(du -h API_OVERVIEW.pdf | cut -f1)"
    echo ""
    echo "To share externally:"
    echo "  - Email: Attach API_OVERVIEW.pdf"
    echo "  - Drive: Upload to shared folder"
    echo "  - Web: Host on static site"
else
    echo "❌ PDF creation failed. Trying alternative method..."
    
    # Alternative: Use pandoc with LaTeX engine
    pandoc drive-bq-indexer/API.md \
        -o API_OVERVIEW.pdf \
        --metadata title="Energy Jibber Jabber API Overview" \
        --metadata author="GB Power Market Team" \
        --toc \
        -V geometry:margin=1in
    
    if [ $? -eq 0 ]; then
        echo "✅ PDF created with LaTeX engine: API_OVERVIEW.pdf"
    else
        echo "❌ Both methods failed. Check pandoc installation."
    fi
fi
