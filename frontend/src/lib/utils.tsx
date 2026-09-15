import { type ClassValue, clsx } from "clsx";
import { BlockMath, InlineMath } from 'react-katex';
// @ts-ignore
import renderMathInElement from 'katex/dist/contrib/auto-render';
import React, { useLayoutEffect, useRef } from 'react';

export function cn(...inputs: ClassValue[]) {
    return clsx(inputs);
}


interface MathHtmlProps {
    html: string;
    className?: string;
    style?: React.CSSProperties;
}

const KATEX_OPTIONS = {
    delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '\\[', right: '\\]', display: true },
        { left: '$', right: '$', display: false },
        { left: '\\(', right: '\\)', display: false },
    ],
    throwOnError: false,
    // Não ignorar td/th para que LaTeX nas células da tabela seja processado
    ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'option'],
};

export const MathHtml: React.FC<MathHtmlProps> = ({ html, className, style }) => {
    const containerRef = useRef<HTMLSpanElement>(null);

    // useLayoutEffect (not useEffect+rAF) so this can't be skipped by a cancelled animation
    // frame, and it runs after EVERY render (no dependency array): some parents re-render on
    // a timer (e.g. the simulado countdown), which makes React re-apply dangerouslySetInnerHTML
    // and reset this span back to raw, un-typeset text even when `html` itself is unchanged.
    // Re-running KaTeX here is cheap and idempotent - it only touches text nodes that still
    // have un-typeset delimiters - so the math stays rendered instead of reverting on the next tick.
    useLayoutEffect(() => {
        const el = containerRef.current;
        if (!el) return;
        renderMathInElement(el, KATEX_OPTIONS);
    });

    return (
        <span
            ref={containerRef}
            className={className}
            style={style}
            dangerouslySetInnerHTML={{ __html: html }}
        />
    );
};

/**
 * Staged tokenizer: order of detection is tables -> block math -> inline math -> bold -> html/text.
 * Whole content between \\[ and \\] (or \\( and \\)) is sent as a single block to KaTeX, so
 * \\mbox{...}, \\mathbb{P}, \\leq, and nested \\begin{array} are preserved and rendered correctly.
 */
type Token =
    | { type: 'table'; raw: string }
    | { type: 'blockmath'; math: string }
    | { type: 'inlinemath'; math: string }
    | { type: 'bold'; inner: string }
    | { type: 'header'; level: number; inner: string }
    | { type: 'html'; raw: string }
    | { type: 'text'; raw: string };

function findMatchingEnd(s: string, start: number, envName: string): number {
    const beginTag = `\\end{${envName}}`;
    const idx = s.indexOf(beginTag, start);
    return idx === -1 ? -1 : idx + beginTag.length;
}

/** KaTeX-supported display environments; \begin{table}, \begin{center}, etc. must NOT be sent to KaTeX */
const MATH_ENVIRONMENTS = new Set([
    'aligned', 'align', 'align*', 'alignat', 'alignat*', 'array', 'Bmatrix', 'bmatrix',
    'cases', 'CD', 'eqnarray', 'eqnarray*', 'equation', 'equation*', 'gather', 'gather*',
    'matrix', 'multline', 'multline*', 'pmatrix', 'smallmatrix', 'split', 'Vmatrix', 'vmatrix',
]);

function tokenizeLatex(content: string): Token[] {
    const tokens: Token[] = [];
    let pos = 0;
    const s = content;

    while (pos < s.length) {
        const rest = s.slice(pos);
        let bestStart = Infinity;
        let bestEnd = pos;
        let bestToken: Token | null = null;

        const consider = (start: number, end: number, token: Token) => {
            if (start < bestStart) {
                bestStart = start;
                bestEnd = end;
                bestToken = token;
            }
        };

        const tableMatch = rest.match(/<table[\s\S]*?<\/table>/i);
        if (tableMatch && tableMatch.index !== undefined) {
            const start = pos + tableMatch.index;
            consider(start, start + tableMatch[0].length, { type: 'table', raw: tableMatch[0] });
        }
        const htmlTagMatch = rest.match(/<([a-zA-Z][a-zA-Z0-9]*)[^>]*>[\s\S]*?<\/\1>/i);
        if (htmlTagMatch && htmlTagMatch.index !== undefined) {
            const start = pos + htmlTagMatch.index;
            consider(start, start + htmlTagMatch[0].length, { type: 'html', raw: htmlTagMatch[0] });
        }
        const blockDollarMatch = rest.match(/\$\$[\s\S]*?\$\$/);
        if (blockDollarMatch && blockDollarMatch.index !== undefined) {
            const start = pos + blockDollarMatch.index;
            consider(start, start + blockDollarMatch[0].length, {
                type: 'blockmath',
                math: blockDollarMatch[0].slice(2, -2).trim(),
            });
        }
        const blockBracketMatch = rest.match(/\\\[[\s\S]*?\\\]/);
        if (blockBracketMatch && blockBracketMatch.index !== undefined) {
            const start = pos + blockBracketMatch.index;
            consider(start, start + blockBracketMatch[0].length, {
                type: 'blockmath',
                math: blockBracketMatch[0].slice(2, -2).trim(),
            });
        }
        const beginMatch = rest.match(/\\begin\{([a-zA-Z0-9*]+)\}/);
        if (beginMatch && beginMatch.index !== undefined) {
            const envName = beginMatch[1];
            if (MATH_ENVIRONMENTS.has(envName)) {
                const start = pos + beginMatch.index;
                const endIdx = findMatchingEnd(s, start + beginMatch[0].length, envName);
                if (endIdx !== -1) {
                    consider(start, endIdx, { type: 'blockmath', math: s.slice(start, endIdx).trim() });
                }
            }
        }
        const inlineParenMatch = rest.match(/\\\([\s\S]*?\\\)/);
        if (inlineParenMatch && inlineParenMatch.index !== undefined) {
            const start = pos + inlineParenMatch.index;
            consider(start, start + inlineParenMatch[0].length, {
                type: 'inlinemath',
                math: inlineParenMatch[0].slice(2, -2).trim(),
            });
        }
        const inlineDollarMatch = rest.match(/\$(?!\$)([^$\n]+?)\$/);
        if (inlineDollarMatch && inlineDollarMatch.index !== undefined) {
            const start = pos + inlineDollarMatch.index;
            consider(start, start + inlineDollarMatch[0].length, {
                type: 'inlinemath',
                math: inlineDollarMatch[1].trim(),
            });
        }
        const boldMatch = rest.match(/\*\*[\s\S]*?\*\*/);
        if (boldMatch && boldMatch.index !== undefined) {
            const start = pos + boldMatch.index;
            consider(start, start + boldMatch[0].length, {
                type: 'bold',
                inner: boldMatch[0].slice(2, -2),
            });
        }
        const headerMatch = rest.match(/^(#{1,6})\s+([^\n]+)/m);
        if (headerMatch && headerMatch.index !== undefined) {
            const start = pos + headerMatch.index;
            consider(start, start + headerMatch[0].length, {
                type: 'header',
                level: headerMatch[1].length,
                inner: headerMatch[2].trim(),
            });
        }

        if (bestToken) {
            if (bestStart > pos) {
                const text = s.slice(pos, bestStart);
                if (text) {
                    tokens.push(
                        /<[a-zA-Z]/.test(text) ? { type: 'html', raw: text } : { type: 'text', raw: text }
                    );
                }
            }
            tokens.push(bestToken);
            pos = bestEnd;
        } else {
            const remainder = s.slice(pos);
            const nextTable = remainder.search(/<table/i);
            const nextBlockDollar = remainder.search(/\$\$/);
            const nextBlockBracket = remainder.search(/\\\[/);
            const nextBegin = remainder.search(/\\begin\{/);
            const nextInlineParen = remainder.search(/\\\(/);
            const nextInlineDollar = remainder.search(/\$(?!\$)/);
            const nextBold = remainder.search(/\*\*/);
            const nextHeader = remainder.search(/^(#{1,6})\s+/m);
            const nextSpecial = Math.min(
                nextTable === -1 ? Infinity : nextTable,
                nextBlockDollar === -1 ? Infinity : nextBlockDollar,
                nextBlockBracket === -1 ? Infinity : nextBlockBracket,
                nextBegin === -1 ? Infinity : nextBegin,
                nextInlineParen === -1 ? Infinity : nextInlineParen,
                nextInlineDollar === -1 ? Infinity : nextInlineDollar,
                nextBold === -1 ? Infinity : nextBold,
                nextHeader === -1 ? Infinity : nextHeader
            );
            const end =
                nextSpecial === Infinity ? s.length : pos + (nextSpecial === 0 ? 1 : nextSpecial);
            const text = s.slice(pos, end);
            if (text) {
                tokens.push(
                    /<[a-zA-Z]/.test(text) ? { type: 'html', raw: text } : { type: 'text', raw: text }
                );
            }
            pos = end;
        }
    }

    return tokens;
}

/** Escapa HTML para uso seguro em MathHtml, preservando \\ e delimitadores LaTeX. */
function escapeHtmlForMath(text: string): string {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

/**
 * Normaliza LaTeX nas células da tabela para o KaTeX processar: delimitadores
 * duplamente escapados (\\\\( \\\\)) e entidade &#92; antes de ( e ).
 */
function normalizeTableLatex(tableHtml: string): string {
    return tableHtml
        .replace(/\\\\\(/g, '\\(')
        .replace(/\\\\\)/g, '\\)')
        .replace(/&#92;\(/g, '\\(')
        .replace(/&#92;\)/g, '\\)');
}

export const renderLatexContent = (content: string, customStyles?: { tableWrapper?: string }) => {
    if (!content) return null;

    const cleanedContent = content
        .replace(/\\newpage|\\vspace\{.*?\}|\\hspace\{.*?\}|\\centering/gi, '')
        .replace(/\\\\\(/g, '\\(')
        .replace(/\\\\\)/g, '\\)');
    const tokens = tokenizeLatex(cleanedContent);

    return tokens.map((t, index) => {
        if (t.type === 'table') {
            const fixedPart = t.raw.replace(/<table([^> \r\n\t])+/i, (match) => {
                if (match.toLowerCase().startsWith('<table') && match.length > 6) {
                    return '<table ' + match.substring(6);
                }
                return match;
            });
            // Garantir delimitadores LaTeX corretos nas células (tabelas vindas do modelo/tool)
            const tableHtml = normalizeTableLatex(fixedPart);
            return (
                <MathHtml
                    key={index}
                    style={{ overflowX: 'auto', margin: '1rem 0', width: '100%', background: 'transparent' }}
                    className={cn("html-table-wrapper", customStyles?.tableWrapper)}
                    html={tableHtml}
                />
            );
        }
        if (t.type === 'blockmath') {
            return (
                <div key={index} className="block-math-wrapper">
                    <BlockMath math={t.math} />
                </div>
            );
        }
        if (t.type === 'inlinemath') {
            return <InlineMath key={index} math={t.math} />;
        }
        if (t.type === 'bold') {
            return (
                <b key={index} style={{ fontWeight: 'bold' }}>
                    {renderLatexContent(t.inner, customStyles)}
                </b>
            );
        }
        if (t.type === 'header') {
            const HeadingTag = `h${t.level}` as React.ElementType;
            return (
                <HeadingTag key={index} style={{ margin: '1rem 0 0.5rem 0', fontWeight: 'bold', fontSize: `${1.4 - (t.level * 0.1)}rem` }}>
                    {renderLatexContent(t.inner, customStyles)}
                </HeadingTag>
            );
        }
        if (t.type === 'html') {
            return <MathHtml key={index} html={t.raw} />;
        }
        // Preservar quebras de linha e processar LaTeX no texto (parágrafos e listas)
        if (t.type === 'text') {
            const parts = t.raw.split(/\n/);
            const escapedContent = parts.map(escapeHtmlForMath).join('<br />');
            return (
                <MathHtml
                    key={index}
                    html={escapedContent}
                    style={{ whiteSpace: 'pre-wrap' }}
                />
            );
        }
        return <span key={index}>{t.raw}</span>;
    });
};

export const renderMessage = (content: string) => {
    return renderLatexContent(content);
};