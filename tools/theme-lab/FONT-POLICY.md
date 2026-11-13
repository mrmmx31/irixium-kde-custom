# Motif FontSet policy — I179

Module: `include/font_policy_motif.h` / `src/font_policy_motif.c`.
Integrated into the view font loader and font sizing. Native measurement reports
a bounded text sample and missing/unsupported glyphs. Personal delivery is pending;
existing personal windows are untouched.

The loader reads the actual first font resolved for the requested FontSet. It asks Xlib which locale charsets are missing, derives those registry/encoding
variants of the same XLFD, checks availability and appends only existing variants
to the original request. This includes Unicode when available. It adopts the candidate only when the first font remains identical and
all95printable ASCII ink/logical extents match. Otherwise the original list remains.
No alternate family, size, spacing, palette or font installation is invented.

Coverage separately checks strictly decoded UTF-8 against the actual Unicode
font's per-character table. FontSet aggregate structures are insufficient;
XLoadQueryFont queries the resolved font and the temporary query is released.
Missing glyphs, supplementary codepoints unsupported by core X11, unavailable
Unicode coverage and malformed UTF-8 are distinct observations. Character presence
is not shaping, bidi correctness or complete-language support. Diagnostics must
never replace, transliterate or modify the user's text. The coverage query is
for explicit diagnosis, not for every keystroke; coverage is shown during native measurement; queries do not hook editing callbacks.

Build: `make build/font-policy-test`; private runtime test: `make check-font-policy`.
The current fixture proves Latin/Greek/Cyrillic presence, CJK missing reporting,
emoji unsupported reporting and rejection of malformed UTF-8. Availability is
server-specific; results cannot be generalized to all machines. Strict C99 build
uses warnings as errors. Native state, four role-palette mapping and editor-history tests are recorded below; delivery remains pending.

## Integration proof and remaining gate

Strict builds, native widget diagnostics and editor history/recovery passed.
Four scheme-input fixtures preserve multilingual clipboard input exactly. This
does not prove four distinct rendered palettes. Xdotool typing altered accented
uppercase/missed a character in the first attempts; failed logs are preserved,
and native clipboard injection now separates text storage from keymap behavior.
The first pixel comparison found a real mapping defect: Greek differed by150
pixels and Cyrillic by128 while Portuguese/ASCII/dash matched. Adding only the
Unicode registry did not supply the missing locale charsets. The loader now asks
Xlib for missing encodings and derives available variants of the same family/size.
After this correction the five sample masks match the direct Unicode glyphs for
UTF8 and multibyte drawing. This is scoped evidence, not complete-language support. No personal application replacement has occurred.

Regression: `make check-font-mapping` compares five native sample masks from
UTF8/multibyte FontSet drawing against directly indexed Unicode glyphs in four
role palettes, with nonempty-ink and distinct-face/text assertions. The current
Motif source TextOut.c uses XmbDrawString for FontSet text. This identifies the
current drawing path, not the exact DomainOS Motif version.

Native status says "absent in the table" explicitly: glyph-table coverage still
requires a render mapping comparison for each supported family/locale. The proof
is scoped to the tested fonts and samples. CJK/supplementary limits stay visible
and text remains intact. Font resizing/widget states were exercised in private native tests. Delivery remains pending.

## Resizing and widget states

The shared sizing loader validates a resolved XLFD and pixels1..128. It retains
family/style and asks the server for the requested size and locale variants.
It rejects an unusable primary font or a FontSet without ink/logical extents;
the view then retains its original native font and reports the actual resource.
A successful name lookup alone is insufficient evidence of usable glyphs.

Native Arm/Disarm and sensitivity changes preserve the exact multilingual label.
Helvetica12/18/24 keeps Portuguese coverage; its Greek/Cyrillic table has15
missing characters in this server. The fixed-family size probes exercise12/18/24,
record the actual font and distinguish missing table coverage from absent runtime.
These tests do not prove complete language rendering at every font size.
An initial assertion that every sized font had full Unicode coverage failed;
it was replaced by reporting actual coverage, never by replacing user text.
