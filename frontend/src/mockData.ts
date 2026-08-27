export interface ChatSession {
    id: string;
    title: string;
    timestamp: string;
}

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    question_data?: {
        id: string;
        number: number;
        assignment: number;
        enunciado: string;
        itens: { codigo: string; enunciado: string }[];
    };
    isError?: boolean;
}

export const mockChats: ChatSession[] = [
    {
        id: '1',
        title: 'Distribuição Normal',
        timestamp: 'Hoje',
    },
    {
        id: '2',
        title: 'Teorema do Limite Central',
        timestamp: 'Ontem',
    },
    {
        id: '3',
        title: 'Variáveis Aleatórias',
        timestamp: '2 dias atrás',
    },
];

export const mockMessages: Message[] = [
    {
        id: '1',
        role: 'assistant',
        content: 'Olá! Sou o TutorPE. Como posso ajudar você com Probabilidade e Estatística hoje?',
        timestamp: '10:00',
    },
    {
        id: '2',
        role: 'user',
        content: 'Pode me explicar a fórmula da Distribuição Normal?',
        timestamp: '10:01',
    },
    {
        id: '3',
        role: 'assistant',
        content: 'Claro! A função densidade de probabilidade da distribuição normal é dada por:\n\n$$ f(x) = \\frac{1}{\\sigma\\sqrt{2\\pi}} e^{-\\frac{1}{2}\\left(\\frac{x-\\mu}{\\sigma}\\right)^2} $$\n\nOnde:\n- $\\mu$ é a média\n- $\\sigma$ é o desvio padrão',
        timestamp: '10:01',
    },
];
