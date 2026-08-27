import type { ParsedEnunciado } from '../types/simulado';

const LABELS = ['A', 'B', 'C', 'D', 'E'];

/**
 * Build ParsedEnunciado from API data. When alternativas (5 strings) is present, use it;
 * otherwise fall back to parsing enunciado string (legacy ")} " format).
 */
export function parseQuestaoForDisplay(
    enunciado: string,
    alternativas?: string[] | null
): ParsedEnunciado {
    if (alternativas && alternativas.length === 5) {
        return {
            statement: enunciado || '',
            alternatives: LABELS.map((label, i) => ({ label, text: alternativas[i] ?? '' })),
        };
    }
    return parseEnunciado(enunciado);
}

/**
 * Parse enunciado string from API (format: "Statement )} Alt1. Alt2. Alt3. Alt4. Alt5.").
 * Returns statement and alternatives with labels A–E. Used when API does not send alternativas.
 */
export function parseEnunciado(enunciado: string): ParsedEnunciado {
    if (!enunciado || typeof enunciado !== 'string') {
        return { statement: '', alternatives: LABELS.map(label => ({ label, text: '' })) };
    }

    const sep = ')}';
    const idx = enunciado.indexOf(sep);
    let statement = enunciado.trim();
    let alternativesText = '';

    if (idx >= 0) {
        statement = enunciado.slice(0, idx + sep.length).trim();
        alternativesText = enunciado.slice(idx + sep.length).trim();
    }

    const alternatives = parseAlternatives(alternativesText);
    return { statement, alternatives };
}

function parseAlternatives(text: string): { label: string; text: string }[] {
    if (!text.trim()) {
        return LABELS.map(label => ({ label, text: '' }));
    }
    const parts = text.split(/\.\s+/).filter(Boolean);
    return LABELS.map((label, i) => {
        let textPart: string;
        if (i === 4 && parts.length > 5) {
            textPart = parts.slice(4).join('. ').trim();
            if (textPart && !textPart.endsWith('.')) textPart += '.';
        } else {
            textPart = parts[i]?.trim() ? parts[i].trim() + (parts[i].trim().endsWith('.') ? '' : '.') : '';
        }
        return { label, text: textPart };
    });
}

/**
 * Extract correct alternative (A–E) from solucao string.
 * Backend pattern: "... )} Falso Falso Verdadeiro Falso Falso" -> position of "Verdadeiro" = index -> A=0, B=1, ...
 */
export function parseGabaritoFromSolucao(solucao: string | undefined): string | null {
    if (!solucao || typeof solucao !== 'string') return null;
    if (!solucao.includes(')}')) return null;
    const partsSplit = solucao.split(')}');
    const after = partsSplit[partsSplit.length - 1];
    if (!after) return null;
    const parts = after.trim().split(/\s+/);
    for (let i = 0; i < parts.length; i++) {
        if (parts[i].includes('Verdadeiro')) {
            const letterIndex = Math.min(i, 4);
            return LABELS[letterIndex];
        }
    }
    return null;
}
