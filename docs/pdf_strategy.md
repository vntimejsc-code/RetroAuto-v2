# PDF Generation Strategy
Since `pandoc` or `wkhtmltopdf` are likely not installed in this environment, we will use the **"Browser-Native PDF"** strategy.

1.  **Concatenate** all v5.0 Markdown files.
2.  **Convert** to HTML using a simple Python script (using `markdown` library if available, or regex).
3.  **Inject CSS** optimized for printing:
    *   `@media print`
    *   Page breaks (`page-break-before: always` for chapters).
    *   Typography (Serif for body, Monospace for code).
4.  **Output:** `docs/RetroAuto_UserGuide_v5.html`.

User Instruction: Open HTML -> Ctrl+P -> Save as PDF.
This yields better results than most backend PDF generators.
