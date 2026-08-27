export interface SimuladoFromApi {
    id: string;
    prova: number;
    dificuldade_media: number;
    concluido: boolean;
    nota: number | null;
    tempo_segundos: number | null;
    created_at: string;
}

export interface QuestaoFromApi {
    id: string;
    order: number;
    conteudo?: number;
    materia: string;
    enunciado: string;
    alternativas?: string[];
    dificuldade: number;
    resposta_usuario: string | null;
    solucao?: string;
    gabarito?: string;
}

export interface CreateSimuladoResponse {
    status: string;
    id: string;
    prova: number;
    dificuldade_media: number;
    concluido: boolean;
    nota: number | null;
    tempo_segundos: number | null;
    created_at: string;
    questions: { id: string; conteudo: number; dificuldade: number; order: number }[];
}

export interface FinalizarSimuladoResponse {
    status: string;
    nota: number;
    acertos: number;
    total: number;
    tempo_segundos: number | null;
}

export interface ParsedEnunciado {
    statement: string;
    alternatives: { label: string; text: string }[];
}
