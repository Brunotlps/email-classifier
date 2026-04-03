# Frontend Improvements

Tracking document for UI/UX improvements identified in the frontend (`frontend/`).
Work is ordered by priority: Critical → High → Medium → Low.

---

## Context

The frontend is a vanilla JS SPA (`index.html` + `js/app.js` + `css/style.css`) with three tabs:
- **Escrever Email** — textarea input, calls `POST /api/v1/classify`
- **Enviar Arquivo** — drag-and-drop file upload, calls `POST /api/v1/classify-file`
- **Histórico** — localStorage history, max 50 items

Results display a classification badge (`produtivo` / `improdutivo`), a confidence bar, reasoning text, and optional response suggestions.

Error handling is currently done via `alert()`. No inline feedback components exist.

---

## Progress

| # | Priority | Status | Description |
|---|---|---|---|
| 1 | Critical | [x] | Fix triple-slash in Railway production URL |
| 2 | Critical | [x] | Fix `border-left` overridden by `border` shorthand on suggestion cards |
| 3 | High | [x] | Fix history preview for file uploads (stores filename, not empty string) |
| 4 | High | [x] | Fix classify button enabled on initial load with 0 characters |
| 5 | High | [x] | Fix drag-and-drop border color using non-existent `--gray-300` variable |
| 6 | High | [x] | Replace `alert()` errors with inline error component |
| 7 | High | [x] | Disable classify buttons during API call to prevent double-submit |
| 8 | High | [x] | Preserve result when switching tabs (don't call `hideResult()` on tab change) |
| 9 | Medium | [x] | Add copy-to-clipboard button on each suggestion card |
| 10 | Medium | [x] | Add explanatory empty state when no suggestions are returned |
| 11 | Medium | [x] | Add semantic color to confidence bar (green/yellow/red thresholds) |
| 12 | Medium | [x] | Clear current file state after classification |
| 13 | Low | [x] | Add ARIA roles and attributes to tab navigation |
| 14 | Low | [x] | Make file upload area keyboard-navigable (tabindex + Enter/Space) |
| 15 | Low | [x] | Add `aria-hidden="true"` to decorative SVG icons |
| 16 | Low | [x] | Update footer tech stack text (remove hardcoded "OpenAI") |
| 17 | Low | [x] | Distinguish network errors from API validation errors — done in High batch |

---

## Detailed Specifications

### Critical

#### #1 — Triple-slash in Railway production URL
- **File**: `frontend/js/app.js:5`
- **Current**: `'https:///email-classifier-production-947c.up.railway.app'`
- **Fix**: `'https://email-classifier-production-947c.up.railway.app'`

#### #2 — `border-left` overridden on suggestion cards
- **File**: `frontend/css/style.css:374-375`
- **Current**:
  ```css
  border-left: 4px solid var(--primary);
  border: 1px solid var(--border-color);   /* overrides border-left above */
  ```
- **Fix**: Merge into a single `border` declaration and restore left accent separately, or reorder so `border-left` comes after `border`.

---

### High

#### #3 — History preview incorrect for file uploads
- **File**: `frontend/js/app.js:334`
- **Current**: `const emailPreview = emailText.value || 'Arquivo enviado';`
- **Issue**: When classifying a file, `emailText.value` is empty. The history entry stores the generic fallback string instead of something useful.
- **Fix**: Pass the file name into `displayResult()` and use it in `saveToHistory()` as the preview label (e.g., `"[arquivo] relatorio.pdf"`).

#### #4 — Classify button enabled on initial load with 0 characters
- **File**: `frontend/index.html:67` / `frontend/js/app.js:148-154`
- **Issue**: The `disabled` attribute is not set in HTML. The event listener only triggers on `input`, so on page load the button is enabled with an empty textarea.
- **Fix**: Add `disabled` attribute directly in the HTML `<button>` tag.

#### #5 — Drag-and-drop border references undefined CSS variable
- **File**: `frontend/js/app.js:172`
- **Current**: `uploadArea.style.borderColor = 'var(--gray-300)';`
- **Issue**: `--gray-300` does not exist in `style.css`. The border color is never restored after a drag-leave or drop event.
- **Fix**: Use `''` to clear the inline style and fall back to the CSS rule, or use `var(--border-color)`.

#### #6 — `alert()` used for all error feedback
- **Files**: `frontend/js/app.js:251`, `frontend/js/app.js:284`
- **Issue**: Native `alert()` is blocking, unstyled, and jarring.
- **Fix**: Add a reusable inline error banner element in the HTML (hidden by default). Show/hide it with a `showError(message)` / `hideError()` helper. Style it in CSS using existing theme variables.

#### #7 — Classify buttons not disabled during API call
- **Files**: `frontend/js/app.js:221-255` (text), `frontend/js/app.js:260-288` (file)
- **Issue**: Both classify buttons remain clickable while a request is in-flight, allowing duplicate submissions.
- **Fix**: Disable the relevant button at the start of the `try` block and re-enable it in `finally`.

#### #8 — Result hidden on every tab switch
- **File**: `frontend/js/app.js:141`
- **Current**: `hideResult()` called on every tab change
- **Issue**: Switching to History and back erases the classification result — counter-intuitive.
- **Fix**: Remove `hideResult()` from the tab switch handler. Only hide the result when a new classification is initiated (`showLoading()`).

---

### Medium

#### #9 — No copy button on suggestion cards
- **Files**: `frontend/js/app.js:316-327`, `frontend/css/style.css:369-397`
- **Fix**: Add a copy icon button to `.suggestion-header`. On click, use `navigator.clipboard.writeText(s.content)` and briefly toggle the icon to a checkmark as visual feedback.

#### #10 — No empty state explanation when suggestions are absent
- **File**: `frontend/js/app.js:329-331`
- **Current**: `suggestionsContainer.style.display = 'none'` with no message
- **Fix**: For `improdutivo` emails with no suggestions, show a short explanatory note (e.g., "No response suggestions for unproductive emails.") instead of silently hiding the section.

#### #11 — Confidence bar has no semantic color coding
- **File**: `frontend/css/style.css:338-343`, `frontend/js/app.js:305-306`
- **Fix**: Apply a CSS class to `.progress-fill` based on confidence value:
  - `≥ 0.75` → green (`var(--success)`)
  - `0.50–0.74` → yellow (`var(--warning)`)
  - `< 0.50` → red (`var(--danger)`)

#### #12 — File state not cleared after classification
- **File**: `frontend/js/app.js:260-288`
- **Issue**: After classifying a file, `currentFile` keeps its value and the UI still shows the filename. Classifying again re-uses the same file with no visual reset.
- **Fix**: After a successful classification, reset `currentFile = null`, clear `selectedFile` content, and reset `fileInput.value`.

---

### Low

#### #13 — Tab navigation lacks ARIA semantics
- **File**: `frontend/index.html:33-51`
- **Fix**: Add `role="tablist"` to `.tabs`, `role="tab"` + `aria-selected` + `aria-controls` to each `.tab` button, and `role="tabpanel"` + `aria-labelledby` to each `.tab-content`.

#### #14 — File upload area not keyboard-accessible
- **File**: `frontend/index.html:77`, `frontend/js/app.js:159`
- **Fix**: Add `tabindex="0"` to `#uploadArea` and a `keydown` listener that triggers `fileInput.click()` on Enter or Space.

#### #15 — Decorative SVGs not hidden from screen readers
- **File**: `frontend/index.html` (multiple SVG elements)
- **Fix**: Add `aria-hidden="true"` to all decorative SVGs. For button SVGs where the button text is present, this is sufficient. For the logo SVG, add a visible or `aria-label` on the parent.

#### #16 — Footer hardcodes "OpenAI" in tech stack
- **File**: `frontend/index.html:174`
- **Current**: `FastAPI • OpenAI • Docker • Railway • Vercel`
- **Fix**: Replace `OpenAI` with the provider-neutral `Ollama / OpenAI` or simply remove the LLM provider from the tech stack line.

#### #17 — No distinction between network errors and API errors
- **Files**: `frontend/js/app.js:249-252`, `frontend/js/app.js:282-285`
- **Fix**: In the `catch` block, check if the error is a `TypeError` (fetch failed / offline) and show a different message than a non-2xx API response.

---

## Implementation notes

- Do not introduce any build tooling, bundlers, or npm dependencies. This is intentional vanilla JS.
- Preserve the existing dark theme CSS variable system — all new styles must use existing `var(--*)` tokens.
- New HTML elements should follow the existing naming conventions (BEM-like class names, Portuguese labels for user-visible text).
- Each priority group should be implemented and verified before moving to the next.
