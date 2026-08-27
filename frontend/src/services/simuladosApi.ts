import API from './api';
import type {
    SimuladoFromApi,
    QuestaoFromApi,
    CreateSimuladoResponse,
    FinalizarSimuladoResponse,
} from '../types/simulado';

const BASE = '/api/simulados';

export async function listSimulados(prova?: number): Promise<SimuladoFromApi[]> {
    const params = prova != null ? { prova } : {};
    const { data } = await API.get<SimuladoFromApi[]>(BASE + '/', { params });
    return data;
}

export async function createSimulado(
    prova: number,
    target_dificuldade?: number
): Promise<CreateSimuladoResponse> {
    const body: { prova: number; target_dificuldade?: number } = { prova };
    if (target_dificuldade != null) body.target_dificuldade = target_dificuldade;
    const { data } = await API.post<CreateSimuladoResponse>(BASE + '/', body);
    return data;
}

export async function getSimulado(id: string): Promise<SimuladoFromApi> {
    const { data } = await API.get<SimuladoFromApi>(`${BASE}/${id}/`);
    return data;
}

export async function getQuestoes(id: string): Promise<QuestaoFromApi[]> {
    const { data } = await API.get<QuestaoFromApi[]>(`${BASE}/${id}/questoes/`);
    return data;
}

export async function submitResposta(
    simuladoId: string,
    question_id: string,
    resposta: string
): Promise<{ status: string; message?: string }> {
    const { data } = await API.post<{ status: string; message?: string }>(
        `${BASE}/${simuladoId}/submeter/`,
        { question_id, resposta: resposta.toUpperCase() }
    );
    return data;
}

export async function finalizarSimulado(
    simuladoId: string,
    tempo_segundos: number
): Promise<FinalizarSimuladoResponse> {
    const { data } = await API.post<FinalizarSimuladoResponse>(
        `${BASE}/${simuladoId}/finalizar/`,
        { tempo_segundos }
    );
    return data;
}

export interface SimuladoChatMessageFromApi {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
}

export interface SimuladoChatPostResponse {
    status: string;
    session_id: string;
    data: {
        items: { type?: string; content?: string }[];
        formatted_content: string;
    };
}

export async function getSimuladoChatMessages(
    simuladoId: string,
    questionId: string
): Promise<SimuladoChatMessageFromApi[]> {
    const { data } = await API.get<SimuladoChatMessageFromApi[]>(
        `${BASE}/${simuladoId}/questoes/${encodeURIComponent(questionId)}/chat/`
    );
    return data;
}

export async function sendSimuladoChatMessage(
    simuladoId: string,
    questionId: string,
    message: string
): Promise<SimuladoChatPostResponse> {
    const { data } = await API.post<SimuladoChatPostResponse>(
        `${BASE}/${simuladoId}/questoes/${encodeURIComponent(questionId)}/chat/`,
        { message }
    );
    return data;
}
