import re


def _normalize_mbox_text(text):
    """
    Normalize and remove \\mbox/\\text so they don't display literally.
    First normalize malformed commands (\\mboxse -> se), then replace known
    \\mbox{...}/\\text{...} with plain text to avoid superfluous mbox in output.
    """
    if not text:
        return text
    # Normalize malformed: \mboxse (no space) -> \mbox{se}, then replace with plain "se"
    text = re.sub(r'\\mbox\s*se\b', 'se', text)
    text = re.sub(r'\\mboxse\b', 'se', text)
    text = re.sub(r'\\mbox\s*caso\s*contr[aáa]rio\b', 'caso contrário', text, flags=re.IGNORECASE)
    text = re.sub(r'\\mboxcasocontr[aáa]rio\b', 'caso contrário', text, flags=re.IGNORECASE)
    text = re.sub(r'\\text\s*se\b', 'se', text)
    text = re.sub(r'\\textse\b', 'se', text)
    # Remove \mbox{se}, \mbox{caso contrário}, \text{se} (replace with plain text)
    text = re.sub(r'\\mbox\{se\}', 'se', text, flags=re.IGNORECASE)
    text = re.sub(r'\\mbox\{caso contrário\}', 'caso contrário', text, flags=re.IGNORECASE)
    text = re.sub(r'\\text\{se\}', 'se', text, flags=re.IGNORECASE)
    return text


def convert_latex_tables(text):
    if not text:
        return text

    captions = re.findall(r'\\caption\{(?P<caption>.*?)\}', text, re.DOTALL)

    # Column-spec patterns that must not appear as cell content (LaTeX table preamble artifacts)
    _COLSPEC_PATTERN = re.compile(r'^\s*[cClCrR|@{}]+\s*$')

    def _clean_table_cell(cell_text):
        """Remove LaTeX artifacts from a single table cell."""
        s = cell_text.strip()
        s = re.sub(r'\\noalign\{[^}]*\}', '', s)
        s = s.strip()
        # Strip single-level decorative braces: {Afirmação} -> Afirmação (avoid breaking math)
        if s.startswith('{') and s.endswith('}') and '{' not in s[1:-1]:
            s = s[1:-1].strip()
        # Cabeçalhos de tabela: X \textbackslash Y -> X/Y (e variantes com nomes de variáveis)
        s = re.sub(r'\s*\\textbackslash\s*', '/', s, flags=re.IGNORECASE)
        s = re.sub(r'\s*/\s*', '/', s)  # colapsar espaços em torno de /
        # Special case for joint probability tables (espaço entre variáveis sem \textbackslash)
        if s == 'X Y':
            s = 'X/Y'
        elif s == 'x y':
            s = 'x/y'
        return s

    def _is_column_spec_only(cell_text):
        """True if cell looks like a column spec (e.g. ccc@{}}, @{}) and should be hidden."""
        s = cell_text.strip()
        if not s:
            return True
        return _COLSPEC_PATTERN.match(s) is not None

    def _table_content_to_html(content):
        """Convert table body (rows separated by \\, cols by &) to HTML table."""
        content = re.sub(r'\\\\\s*\[.*?\]', r'\\\\', content)
        content = re.sub(r'\\hline|\\toprule|\\midrule|\\bottomrule', '', content)
        rows = re.split(r'\\\\', content)
        html_rows = []
        for row in rows:
            row = row.strip()
            if not row:
                continue
            cols = re.split(r'&', row)
            html_cols = []
            for col in cols:
                clean_col = _clean_table_cell(col)
                # Skip cells that are only column-spec artifacts
                if _is_column_spec_only(clean_col):
                    clean_col = ''
                html_cols.append(f'<td>{clean_col}</td>')
            # Skip rows that are entirely column-spec cells
            if all(_is_column_spec_only(_clean_table_cell(c.strip())) for c in cols):
                continue
            html_rows.append(f'  <tr>{" ".join(html_cols)}</tr>')
        if not html_rows:
            return ""
        return f'<table border="1">{"".join(html_rows)}</table>'

    def _tabular_to_html(match):
        return _table_content_to_html(match.group('content'))

    def _longtable_to_html(match):
        content = match.group('content')
        content = re.sub(r'\\noalign\{[^}]*\}', '', content)
        content = re.sub(r'\\endhead|\\endfirsthead|\\endfoot|\\endlastfoot', '', content)
        return _table_content_to_html(content)

    tabular_pattern = re.compile(
        r'\\begin\{tabular[*x]?\}\s*(?:\[[^\]]*\])*\s*(?:\{(?:[^{}]+|\{[^{}]*\})*\})*\s*(?P<content>.*?)\\end\{tabular[*x]?\}',
        re.DOTALL
    )
    longtable_pattern = re.compile(
        r'\\begin\{longtable\}\s*(?:\[[^\]]*\])*\s*(?:\{(?:[^{}]+|\{[^{}]*\})*\})*\s*(?P<content>.*?)\\end\{longtable\}',
        re.DOTALL
    )

    text = longtable_pattern.sub(_longtable_to_html, text)
    text = tabular_pattern.sub(_tabular_to_html, text)
    
    text = re.sub(r'\\begin\{table\}(\[.*?\])?', '', text)
    text = re.sub(r'\\end\{table\}', '', text)
    text = re.sub(r'\\centering|\\footnotesize|\\small|\\large|\\Huge|\\huge|\\tiny', '', text)
    text = re.sub(r'\\begin\{center\}|\\end\{center\}|\\begin\{flushleft\}|\\end\{flushleft\}|\\begin\{flushright\}|\\end\{flushright\}', '', text)
    text = re.sub(r'\\scalebox\{.*?\}\s*\{', '', text)
    # Remove trailing brace from scalebox if it follows a table
    text = re.sub(r'(<\/table>)\s*\}', r'\1', text)
    
    # Handle the captured captions
    text = re.sub(r'\\caption\{.*?\}', '', text, flags=re.DOTALL)
    text = re.sub(r'\\label\{.*?\}', '', text, flags=re.DOTALL)
    
    if captions:
        # Insert first caption into first table found
        caption_tag = f'<caption style="caption-side: top; font-weight: bold; margin-bottom: 8px;">{captions[0]}</caption>'
        text = re.sub(r'(<table.*?>)', r'\1' + caption_tag, text, count=1)
    
    return text

def clean_latex(text):
    if not text:
        return text

    # Normalize \mbox and \text so KaTeX can render (e.g. \mboxse -> \mbox{se})
    text = _normalize_mbox_text(text)

    # Normalizar \$ como delimitador de matemática para $ (modelo às vezes envia escapado)
    text = re.sub(r'\\\$\\\$', '$$', text)  # block $$ 
    text = re.sub(r'\\\$([^$]+?)\\\$', r'$\1$', text)  # inline $ ... $

    # Protect HTML table blocks first (they can contain % e.g. "width: 100%" which would
    # be wrongly stripped as LaTeX comment by the %-removal below)
    html_table_blocks = []
    def _protect_html_table(match):
        placeholder = f"____HTML_TABLE_{len(html_table_blocks)}____"
        html_table_blocks.append(match.group(0))
        return placeholder

    text = re.sub(r'<table[\s\S]*?</table>', _protect_html_table, text, flags=re.IGNORECASE)

    # Protect math blocks during cleaning
    math_blocks = []
    def _protect_math(match):
        placeholder = f"____MATH_BLOCK_{len(math_blocks)}____"
        math_blocks.append(match.group(0))
        return placeholder

    # Remove LaTeX comments (would otherwise strip e.g. "100%; margin:..." after "width: 100")
    text = re.sub(r'(?<!\\)%.*$', '', text, flags=re.MULTILINE)

    # 1. Convert tables BEFORE protecting math, so \begin{table}...\end{table} and
    # \begin{tabular} are converted to HTML and not mistaken for math blocks.
    text = convert_latex_tables(text)

    # 2. Protect math blocks: do not add substitutions above that could corrupt \] or \).
    # Block/inline math are preserved as-is (including \mbox{...}, \mathbb{P}, nested \begin{array}).
    math_patterns = [
        r'\\begin\{(?P<env>(?!itemize|enumerate|description|center|flushleft|flushright|minipage)[a-zA-Z0-9\*]+?)\}[\s\S]*?\\end\{(?P=env)\}',  # Math environments
        r'\\\[[\s\S]*?\\\]',   # Block math \[ ... \] (first \] closes)
        r'\\\(.*?\\\)',        # Inline math \( ... \)
        r'\$\$[\s\S]*?\$\$',   # Block math $$ ... $$
        r'\$[^$\n]+?\$',       # Inline math $ ... $
    ]
    combined_pattern = f'({"|".join(math_patterns)})'
    text = re.sub(combined_pattern, _protect_math, text)
    
    # 2. Convert remaining captions/labels if they appear outside tables
    text = re.sub(r'\\caption\{(?P<content>.*?)\}', r'<p style="text-align:center; font-weight:bold;">\g<content></p>', text, flags=re.DOTALL)
    text = re.sub(r'\\label\{.*?\}', '', text)
    
    # 2. Convert raw number grids (text with \ \ separators not in tabular)
    def _raw_grid_to_table(match):
        grid_content = match.group(1).strip()
        rows = re.split(r'\\\\', grid_content)
        html_rows = []
        for row in rows:
            row = row.strip()
            if not row: continue
            # Split by LaTeX spaces \ \ or single \ or &
            cols = re.split(r'\\(?:\s+\\)*|&', row)
            html_cols = []
            for col in cols:
                col = col.strip()
                if col:
                    # Preserve math inside cells
                    html_cols.append(f'<td style="padding: 0 15px; border: none;">{col}</td>')
            if html_cols:
                html_rows.append(f'<tr>{" ".join(html_cols)}</tr>')
        
        if not html_rows: return match.group(0)
        return f'<table border="0" style="border-collapse: collapse; margin: 15px auto; width: auto;">{"".join(html_rows)}</table>'

    # Look for multi-line blocks with backslash separators (common in \begin{center})
    # that aren't already part of a table. We only want this if it looks like a grid (contains & or multiple \\)
    grid_pattern = r'((?:[^\n]*?(?:&|\\(?:\s+\\)+|\\\\)[^\n]*?(?:\n|$)){2,})'
    text = re.sub(grid_pattern, _raw_grid_to_table, text)

    # 3. Basic formatting
    text = re.sub(r'\\textbf\{(?P<content>.*?)\}', r'<b>\g<content></b>', text, flags=re.DOTALL)
    text = re.sub(r'\\textit\{(?P<content>.*?)\}', r'<i>\g<content></i>', text, flags=re.DOTALL)
    text = re.sub(r'\\emph\{(?P<content>.*?)\}', r'<em>\g<content></em>', text, flags=re.DOTALL)
    
    # Handle old-style bold/italic: {\bf text}
    text = re.sub(r'\{\\bf\s+(?P<content>.*?)\}', r'<b>\g<content></b>', text, flags=re.DOTALL)
    text = re.sub(r'\{\\it\s+(?P<content>.*?)\}', r'<i>\g<content></i>', text, flags=re.DOTALL)

    # 3. Common LaTeX characters
    text = text.replace('~', ' ')
    # \% -> % so percentages display without backslash
    text = text.replace('\\%', '%')
    
    # 4. Handle lists
    def _convert_itemize(match):
        inner = match.group(1)
        items = re.findall(r'\\item\s+(.*?)(?=\\item|\Z)', inner, re.DOTALL)
        if not items: return ""
        html_items = "".join([f"<li>{item.strip()}</li>" for item in items])
        return f"<ul>{html_items}</ul>"
        
    text = re.sub(r'\\begin\{itemize\}(.*?)\\end\{itemize\}', _convert_itemize, text, flags=re.DOTALL)

    def _convert_enumerate(match):
        inner = match.group(1)
        items = re.findall(r'\\item\s+(.*?)(?=\\item|\Z)', inner, re.DOTALL)
        if not items: return ""
        html_items = "".join([f"<li>{item.strip()}</li>" for item in items])
        return f"<ol>{html_items}</ol>"
        
    text = re.sub(r'\\begin\{enumerate\}(.*?)\\end\{enumerate\}', _convert_enumerate, text, flags=re.DOTALL)

    text = re.sub(r'\\newpage|\\vspace\{.*?\}|\\hspace\{.*?\}', '', text)
    # Apenas quebra de linha LaTeX (duas barras): \\ no fim de linha -> <br>. Nunca tocar em \frac, \leq, etc.
    text = re.sub(r'(?<!<br>)\\\\ *(\n|$)', r'<br>\1', text)

    # Envolver comandos de matemática inline em texto (fora de blocos math) com $ $ para o frontend renderizar
    def _wrap_inline_math(segment):
        if re.match(r'____MATH_BLOCK_\d+____$', segment):
            return segment
        # \boldsymbol{...} -> $\boldsymbol{...}$
        segment = re.sub(
            r'(?<!\$)\\boldsymbol\{((?:[^{}]|\{[^{}]*\})*)\}',
            r'$\boldsymbol{\1}$',
            segment,
        )
        # \hat{...}, \bar{...}, \tilde{...}, \widehat{...} -> $...$ (\\ na substituição = barra literal, evita re.error "bad escape \h")
        for cmd in (r'\hat', r'\bar', r'\tilde', r'\widehat'):
            segment = re.sub(
                rf'(?<!\$){re.escape(cmd)}\{{((?:[^{{}}]|\{{[^{{}}]*\}})*)\}}',
                r'$\\' + cmd[1:] + r'{\1}$',
                segment,
            )
        # Símbolos gregos isolados: \lambda, \mu, \sigma_1, etc.
        segment = re.sub(
            r'(?<!\$)(\\(?:lambda|mu|sigma|theta|alpha|beta|gamma|delta|omega)(?:_\{[^{}]*\})?)(?!\w)',
            r'$\1$',
            segment,
        )
        return segment

    parts = re.split(r'(____MATH_BLOCK_\d+____)', text)
    text = ''.join(_wrap_inline_math(p) for p in parts)

    for i, content in enumerate(math_blocks):
        # Strip layout commands from math blocks too
        content = re.sub(r'\\newpage|\\vspace\{.*?\}|\\hspace\{.*?\}', '', content)
        # Manter \\ para quebra de linha em cases/array; não usar \\[0.5em] para não ser confundido com delimitador \[ ... \] no frontend
        placeholder = f"____MATH_BLOCK_{i}____"
        text = text.replace(placeholder, content)

    # Restore protected HTML table blocks (so % and other LaTeX rules did not alter them)
    for i, content in enumerate(html_table_blocks):
        text = text.replace(f"____HTML_TABLE_{i}____", content)

    # Final cleanup of stray LaTeX artifacts
    text = re.sub(r'\\begin\{itemize\}|\\end\{itemize\}|\\begin\{enumerate\}|\\end\{enumerate\}', '', text)
    # Remove \def\labelenumii{...} and similar (full form with balanced braces)
    text = re.sub(r'\\def\\labelenumii\s*\{(?:[^{}]|\{[^{}]*\})*\}', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\\def\\labelenum[i]+\s*\{(?:[^{}]|\{[^{}]*\})*\}', '', text, flags=re.IGNORECASE)
    # Truncated form (e.g. \def\labelenumii{(\alph{enumii} without closing) or up to first }
    text = re.sub(r'\\def\\labelenumii\s*\{[^}]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\\def\\labelenum[i]+\s*\{[^}]*', '', text, flags=re.IGNORECASE)
    # Leftover literal from labelenumii artifact when it appears as plain text
    text = re.sub(r'\(\s*\\alph\s*\{\s*enumii\s*\}\s*\)?\s*', '', text, flags=re.IGNORECASE)

    text = re.sub(r'(\$\$?)\s*(<table.*?>.*?<\/table>)\s*\1', r'\2', text, flags=re.DOTALL | re.IGNORECASE)

    # Remove superfluous trailing closing brace (e.g. left over from \cases or other env)
    text = re.sub(r'\}\s*$', '', text)

    # Converter matemática inline $...$ para \(...\) na saída, forma que o frontend interpreta como inlinemath
    text = re.sub(r'\$(?!\$)([^$\n]+?)\$(?!\$)', r'\\(\1\\)', text)

    # Normalizar delimitadores duplamente escapados para o formato esperado pelo KaTeX no frontend
    # Usar \\x28/\\x29 para ( e ) no padrão e evitar que ( inicie subpattern
    text = re.sub(r'\\\\\x28', r'\\(', text)
    text = re.sub(r'\\\\\x29', r'\\)', text)

    return text.strip()
