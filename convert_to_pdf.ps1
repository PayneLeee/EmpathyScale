# Markdown to PDF Converter Script
# Automatically detects available tools and converts the scale draft files

$ErrorActionPreference = "Stop"

Write-Host "=== Markdown to PDF Converter ===" -ForegroundColor Cyan
Write-Host ""

# File paths
$coAssemblyMd = "data\runs\2025-10-31_131000\empathy_scale_generation_agent_group\scale_draft.md"
$chatCollabMd = "data\runs\2025-10-31_132506\empathy_scale_generation_agent_group\scale_draft.md"

$coAssemblyPdf = $coAssemblyMd -replace '\.md$', '.pdf'
$chatCollabPdf = $chatCollabMd -replace '\.md$', '.pdf'

# Check if files exist
if (-not (Test-Path $coAssemblyMd)) {
    Write-Host "❌ File not found: $coAssemblyMd" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $chatCollabMd)) {
    Write-Host "❌ File not found: $chatCollabMd" -ForegroundColor Red
    exit 1
}

# Method 1: Try Pandoc
$pandocAvailable = $false
try {
    $null = Get-Command pandoc -ErrorAction Stop
    $pandocAvailable = $true
    Write-Host "✓ Pandoc found!" -ForegroundColor Green
} catch {
    Write-Host "⚠ Pandoc not found. Trying alternative methods..." -ForegroundColor Yellow
}

if ($pandocAvailable) {
    Write-Host ""
    Write-Host "Converting using Pandoc..." -ForegroundColor Cyan
    
    # Check if LaTeX is available
    $xelatexAvailable = $false
    try {
        $null = Get-Command xelatex -ErrorAction Stop
        $xelatexAvailable = $true
    } catch {
        Write-Host "⚠ XeLaTeX not found. Trying pdftex..." -ForegroundColor Yellow
    }
    
    $pdfEngine = if ($xelatexAvailable) { "xelatex" } else { "pdftex" }
    
    try {
        # Convert Co-Assembly
        Write-Host "  Converting Co-Assembly scale..." -ForegroundColor Gray
        pandoc $coAssemblyMd -o $coAssemblyPdf --pdf-engine=$pdfEngine -V geometry:margin=1in -V fontsize=12pt
        Write-Host "  ✓ $coAssemblyPdf" -ForegroundColor Green
        
        # Convert Chat Collaboration
        Write-Host "  Converting Chat Collaboration scale..." -ForegroundColor Gray
        pandoc $chatCollabMd -o $chatCollabPdf --pdf-engine=$pdfEngine -V geometry:margin=1in -V fontsize=12pt
        Write-Host "  ✓ $chatCollabPdf" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "✅ Conversion completed successfully!" -ForegroundColor Green
        exit 0
    } catch {
        Write-Host "❌ Pandoc conversion failed: $_" -ForegroundColor Red
        Write-Host "Trying Python method..." -ForegroundColor Yellow
    }
}

# Method 2: Try Python
Write-Host ""
Write-Host "Trying Python method..." -ForegroundColor Cyan

$pythonAvailable = $false
try {
    $pythonVersion = python --version 2>&1
    $pythonAvailable = $true
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠ Python not found" -ForegroundColor Yellow
}

if ($pythonAvailable) {
    try {
        # Check if required packages are installed
        python -c "import markdown, weasyprint" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠ Required packages not found. Installing..." -ForegroundColor Yellow
            pip install markdown weasyprint
        }
        
        Write-Host "  Running Python conversion script..." -ForegroundColor Gray
        python convert_md_to_pdf.py
        
        if (Test-Path $coAssemblyPdf) {
            Write-Host ""
            Write-Host "✅ Conversion completed successfully!" -ForegroundColor Green
            exit 0
        }
    } catch {
        Write-Host "❌ Python conversion failed: $_" -ForegroundColor Red
    }
}

# If all methods failed
Write-Host ""
Write-Host "❌ All conversion methods failed!" -ForegroundColor Red
Write-Host ""
Write-Host "Please try one of these options:" -ForegroundColor Yellow
Write-Host "  1. Install Pandoc: winget install JohnMacFarlane.Pandoc" -ForegroundColor White
Write-Host "  2. Install MiKTeX: winget install MiKTeX.MiKTeX" -ForegroundColor White
Write-Host "  3. Use online tool: https://dillinger.io/" -ForegroundColor White
Write-Host "  4. Install Python packages: pip install markdown weasyprint" -ForegroundColor White
exit 1

