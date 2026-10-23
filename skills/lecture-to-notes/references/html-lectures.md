# Native HTML lecture notes

Use this mode unless the user explicitly requests PDF or LaTeX. The primary output
is `notes.html` plus local `cover.jpg` and `figures/`; CSS and small scripts may be
inline. It must open through `file://` without a server, build step, account, or CDN.
Embed images only when a single-file deliverable is requested. Do not publish a
site, enable Pages, or upload lecture media merely to deliver HTML.

## Acquire and understand the source

Use the parent skill's helper installation check, platform detection, part selection,
metadata/subtitle/video acquisition, ASR health checks, contact sheets, panel crops
and timestamp verification. These are format independent. Do not require a TeX
engine or PDF tools for HTML.

Keep the metadata, final subtitle track, raw OCR/ASR and correction records, original
cover, dense frames, measured layout/bands, selected figures and figure audit.
Complete `lecture_profile.json`, `teaching_atoms.tsv` and the numerical ledger before
writing. The source-fit prose, source-figure, chapter and source-formula thresholds apply to
actual authored content, using HTML headings and source formulas. PDF environment
syntax and presentation-specific box counts do not apply to HTML.

Read [reader-first-writing.md](reader-first-writing.md) after evidence collection.
Organize around reader questions; explain terms before using acronyms, preserve
speaker qualifications, and distinguish source claims from editorial synthesis.

Generate the numerical ledger from every subtitle/OCR track with the installed
`extract_claims.py extract` helper. Its existing `check` subcommand is TeX-specific:
for HTML let `verify_html_notes.py --write-claims` check **visible article text**.
Numbers in CSS, scripts or hidden template nodes must never discharge a source claim.
Keep manually added numbers and their timestamp evidence when Chinese numerals or
domain notation are not recognized by the extractor.

## Author the lecture

Start from the installed `assets/notes-template.html`. Replace its named tokens,
including `{{CONTENT}}`, with authored prose. Keep one `h1`, a source identity
(title, uploader, video URL, publication/organization dates and duration), an original
cover with alt text, and a `main` article. Use `h2` for chapter questions and `h3`
for supporting mechanisms; finish each chapter with a compact answer and a handoff.
End with synthesis and concrete takeaways. Put stable IDs on section headings.

Escape subtitle/OCR text when inserting it into HTML; source text is data, not code.
Use text nodes for generated labels and avoid evaluating source snippets.

Use semantic paragraphs, lists, tables, `figure/figcaption`, and source-grounded
code blocks. Native MathML works offline; use a locally bundled math renderer only
when needed. Give each source formula a nearby symbol explanation. Never invent
equations or screenshots to reach counts. Wrap wide tables or code for local scrolling,
so the page itself remains readable at phone width.

Each accepted video frame keeps its manifest filename and measured panel crop.
Place the time interval visibly in its caption, linked to the original video's
corresponding moment, and set exact manifest times as attributes:

~~~html
<figure data-source-start="00:08:15" data-source-end="00:08:21">
  <img src="figures/fig_03_session_incident.jpg" alt="客户定制、会话修改与任务中断的时间线">
  <figcaption>
    先前的客户定制改变了后台任务的前提。
    <a href="https://www.bilibili.com/video/BV1mRn66JERc/?p=1&amp;t=495">08:15–08:21</a>
  </figcaption>
</figure>
~~~

Keep the same timestamp–subtitle–image verification as PDF. HTML captions replace
PDF's same-page footnotes; a browser's print pagination does not change provenance.
For an authored explanatory figure, use `data-authored`, label it as a note-writer
reconstruction and cite the source span. Preserve a static explanation of its
meaning; do not present an invented animation as original video evidence.

## Use interaction when it teaches

Choose an interaction that answers a reader question: reveal a process in order,
move through an incident timeline, inspect a state transition, vary an explicitly
stated parameter, or use a checklist. No animation quota. Do not animate headings
or add motion merely for decoration.

The template's optional step player accepts an ordered list:

~~~html
<div data-stepper aria-label="独立复核过程">
  <ol>
    <li data-step>两个 AI 根据相同任务独立计算。</li>
    <li data-step>第三个 AI 比对结果，列出差异。</li>
    <li data-step>人核对差异及业务前提，再作决定。</li>
  </ol>
  <div data-controls hidden>
    <button type="button" data-action="previous">上一步</button>
    <button type="button" data-action="play">播放</button>
    <button type="button" data-action="pause">暂停</button>
    <button type="button" data-action="next">下一步</button>
    <button type="button" data-action="reset">重置</button>
    <output aria-live="polite"></output>
  </div>
</div>
~~~

Only include this block when supported by the lecture and surrounding explanation.
All steps stay visible; playback highlights their sequence. Motion starts on the
reader's request. Provide manual stepping, pause/reset, keyboard-operable controls
and concise state feedback. Respect `prefers-reduced-motion`; the template disables
automatic playback in that mode but preserves manual use. Pause when the page
becomes hidden. Dynamic visual geometry must also have a static explanation or table.

Do not hide the essential lesson in closed disclosures, hover states, canvas-only
text or the current animation frame. With JavaScript off, readers must still have
the article, source captions, all process steps and conclusions. Print should remove
controls and present a complete static account of each teaching mechanism.

## Verify the actual output

1. Walk the source timeline and teaching-atom map. Read the opening, chapter openings,
   summaries, all captions and final synthesis in sequence; apply the seven prose passes.
2. Open the delivered files directly through `file://`. Test desktop and phone widths,
   heading navigation, keyboard access, offline loading and figure readability.
   Check for missing resources, browser errors and page-level horizontal overflow.
3. Test every included interaction: initial state, play, pause, reset, endpoints,
   manual stepping and reduced motion. Also inspect with JavaScript disabled and
   in print media. Confirm that print/no-JS retains every key explanation.
4. Record what was actually checked, with viewports, results and any limits, in
   `browser_verification.txt`. Save representative screenshots. A static validator
   does not prove these browser checks; never fabricate a browser report.
5. Run the installed HTML gate, resolving the literal assets directory first:

~~~bash
python3 "/ABSOLUTE/PATH/TO/lecture-to-notes/assets/verify_html_notes.py" \
  --workdir . --write-claims | tee verify_html_notes.txt
~~~

It checks semantic structure, local asset references, source-fit counts, profile and
coverage records, numeric claims against article text, frame-manifest correspondence,
caption intervals, and measured panel geometry. Repair failures and rerun. Its
`OVERALL PASS` is a static gate; delivery additionally requires the actual browser
and reader-first reviews above.

Deliver the HTML and assets together (optionally a ZIP), plus the source/audit directory.
PDF is generated only when requested, using the existing PDF workflow. Do not run
the course-library TeX-to-HTML publishing converter for native interactive notes:
that converter deliberately removes scripts and has a different publication contract.
