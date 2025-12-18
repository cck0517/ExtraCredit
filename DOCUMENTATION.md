# CS 182/282A Special Participation A - Blue Team Enhanced Documentation

## Project Summary

This project creates a searchable website documenting student submissions for **Special Participation A**: evaluating LLM performance on deep learning homework assignments.

## Blue Team Enhancements Over Red Team Baseline

### Data Quality Improvements
1. **LLM Name Normalization** - Canonical mapping ensures consistent filtering
   - "Claude 4.5" → "Claude Opus 4.5"
   - "GPT-5.1 Pro" and "GPT 5.1 Pro" → consistent format
   - 14 different variations normalized

2. **Homework Format Standardization** - All homework IDs use "HW#" format
   - "HW08" → "HW8" (no leading zeros)
   - Proper numeric sorting

3. **Link Extraction** - External chat share links extracted
   - Claude AI share links
   - DeepSeek share links
   - Grok share links
   - Mistral chat links
   - Google Drive links

4. **Student Profile Extraction** - GitHub, LinkedIn, personal website URLs

### JavaScript Fixes & Features
5. **Fixed Deprecated Event Bug** - app.js no longer uses global `event` object
6. **Dynamic Statistics** - Overview stats computed from data, not hardcoded
7. **Sorting Options** - Sort by date, views, author, or LLM
8. **URL Parameter Support** - Direct linking with `?thread=ID`, `?llm=NAME`, `?hw=HW#`
9. **Default Content** - Filter sections show all submissions by default
10. **Error Handling** - Graceful error messages if data fails to load
11. **IIFE Pattern** - Proper JavaScript encapsulation

### Accessibility (WCAG 2.1)
12. **Skip Link** - Keyboard users can skip to main content
13. **Focus Styles** - Visible focus indicators on all interactive elements
14. **ARIA Labels** - Proper labeling for screen readers
15. **Semantic HTML** - Proper heading hierarchy and landmarks
16. **Visually Hidden** - Screen reader text for context

### CSS & UX Improvements
17. **Dark Mode** - Automatic via `prefers-color-scheme`
18. **Print Styles** - Clean printing without navigation
19. **Removed Duplicate Selector** - CSS code quality fix
20. **Focus-Visible** - Only show focus ring for keyboard navigation

## What Was Done by AI (Claude Code with Opus 4.5)

### Phase 1: Review & Analysis
- Thoroughly reviewed Red Team codebase
- Identified 14 categories of issues and improvements
- Created detailed implementation plan

### Phase 2: Data Processing Enhancements
- Added `LLM_NORMALIZATION` dictionary to `process_threads.py`
- Added `normalize_llm_name()` function with partial matching
- Added `extract_links()` for chat share URLs
- Added `extract_student_profiles()` for GitHub/LinkedIn/website
- Regenerated `data.js` with clean, normalized data

### Phase 3: JavaScript Improvements
- Completely rewrote `app.js` with all fixes
- Added sorting functionality with dropdown
- Added URL parameter handling
- Fixed deprecated global event usage
- Added error handling and loading states

### Phase 4: CSS Enhancements
- Added dark mode support via CSS variables
- Added skip link styles
- Added visually-hidden class
- Added focus-visible styles
- Added print stylesheet
- Fixed duplicate selector issue

### Phase 5: HTML Updates
- Added skip link for accessibility
- Added ARIA labels and roles
- Added meta description for SEO
- Added proper landmark regions
- Updated footer with Blue Team branding

## Statistics (After Enhancement)

- **Total Submissions**: 21
- **Unique Students**: 21
- **LLMs Evaluated**: 14 (normalized from 17+ variations)
  - Claude Opus 4.5
  - Claude Sonnet 4.5
  - GPT-4o
  - GPT-5.1 Pro
  - GPT-5.1 Thinking
  - GPT-5.1 Extended Thinking
  - DeepSeek
  - DeepSeek v3.2
  - Gemini 2.5 Flash
  - Gemini 3 Pro
  - Gemma 3
  - Grok
  - Mistral
  - Unknown LLM (1 submission with unclear attribution)
- **Homework Coverage**: HW0 through HW13
- **Attachments**: PDF files linked per submission
- **External Links**: 7 chat share links extracted

## Files Modified (Blue Team Changes)

```
process_threads.py   # Added normalization, link extraction, profile extraction
website/
├── index.html       # Added accessibility, ARIA, meta tags, Blue Team footer
├── styles.css       # Added dark mode, skip link, focus styles, print styles
├── app.js           # Complete rewrite with fixes and new features
└── data.js          # Regenerated with normalized data
```

## New Features Summary

| Feature | Description |
|---------|-------------|
| Sorting | Sort submissions by date, views, author, or LLM |
| URL Params | Deep link to specific submissions or filters |
| Dark Mode | Automatic based on system preference |
| Accessibility | WCAG 2.1 compliant with skip links, focus styles |
| Profile Links | GitHub/LinkedIn icons when available |
| Chat Links | Direct links to AI conversation transcripts |

## How to Run

```bash
cd /mnt/sky-gh200/fangzhou/ExtraCredit/website
python -m http.server 8080
# Open http://localhost:8080 in browser
```

## How to Regenerate Data

```bash
cd /mnt/sky-gh200/fangzhou/ExtraCredit
uv run python process_threads.py
```

## Test Cases

1. **Search**: Type "Claude" in search box → shows Claude submissions
2. **LLM Filter**: Click "DeepSeek" → filters to DeepSeek submissions
3. **HW Filter**: Click "HW8" → filters to HW8 submissions
4. **Sorting**: Select "Most Views" → reorders by view count
5. **Direct Link**: Add `?thread=7451901` to URL → opens modal
6. **Dark Mode**: Set OS to dark mode → colors adjust
7. **Keyboard**: Tab through page → focus ring visible
8. **Skip Link**: Tab once → "Skip to main content" appears

## Credits

- **Blue Team Implementation**: AI-assisted (Claude Code with Opus 4.5)
- **Human Guidance**: Task specification and approval
- **Course**: CS 182/282A Deep Learning, UC Berkeley, Fall 2025
