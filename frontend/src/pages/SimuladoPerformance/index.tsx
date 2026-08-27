import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Bot, ChevronDown, ChevronUp } from 'lucide-react';
import 'katex/dist/katex.min.css';
import styles from './SimuladoPerformance.module.scss';
import { cn, renderLatexContent } from '../../lib/utils';
import { QuestionChat } from '../../components/QuestionChat';
import { getSimulado, getQuestoes } from '../../services/simuladosApi';
import type { SimuladoFromApi, QuestaoFromApi } from '../../types/simulado';
import { parseQuestaoForDisplay, parseGabaritoFromSolucao } from '../../lib/parseEnunciado';

export const SimuladoPerformance: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [openChats, setOpenChats] = useState<Record<string, boolean>>({});
    const [closingChatId, setClosingChatId] = useState<string | null>(null);
    const [openingChatId, setOpeningChatId] = useState<string | null>(null);
    const [simulado, setSimulado] = useState<SimuladoFromApi | null>(null);
    const [questions, setQuestions] = useState<QuestaoFromApi[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!id) return;
        setLoading(true);
        setError(null);
        Promise.all([getSimulado(id), getQuestoes(id)])
            .then(([sim, qs]) => {
                setSimulado(sim);
                setQuestions(qs);
            })
            .catch((err) => {
                const msg = err.response?.data?.error ?? err.message ?? 'Erro ao carregar desempenho.';
                setError(msg);
            })
            .finally(() => setLoading(false));
    }, [id]);

    useEffect(() => {
        if (!simulado || loading) return;
        if (!simulado.concluido) {
            navigate(`/simulados/${id}/play`, { replace: true });
        }
    }, [simulado, loading, id, navigate]);

    const toggleChat = (questionId: string) => {
        setOpenChats((prev) => ({ ...prev, [questionId]: !prev[questionId] }));
    };

    const startOpenChat = (questionId: string) => {
        setOpenChats((prev) => ({ ...prev, [questionId]: true }));
        setOpeningChatId(questionId);
    };

    const startCloseChat = (questionId: string) => {
        setClosingChatId(questionId);
    };

    useEffect(() => {
        if (!openingChatId) return;
        requestAnimationFrame(() => {
            requestAnimationFrame(() => setOpeningChatId(null));
        });
    }, [openingChatId]);

    const handleChatCloseAnimationEnd = (e: React.TransitionEvent) => {
        if (e.propertyName !== 'max-height' || !closingChatId) return;
        setOpenChats((prev) => ({ ...prev, [closingChatId]: false }));
        setClosingChatId(null);
    };

    if (loading) {
        return (
            <div className={styles.performance}>
                <div className={styles.performance__loading}>Carregando...</div>
            </div>
        );
    }
    if (error || !simulado) {
        return (
            <div className={styles.performance}>
                <div className={styles.performance__error}>
                    {error ?? 'Simulado não encontrado.'}
                </div>
            </div>
        );
    }
    if (!simulado.concluido) {
        return null;
    }

    const correctCount = questions.filter((q) => {
        const gabarito = q.gabarito || parseGabaritoFromSolucao(q.solucao);
        return gabarito && q.resposta_usuario?.toUpperCase() === gabarito;
    }).length;
    const total = questions.length;
    const scorePercent = total > 0 ? Math.round((simulado.nota ?? 0) * 10) : 0;

    return (
        <div className={styles.performance}>
            <header className={styles.performance__header}>
                <button type="button" onClick={() => navigate('/simulados')}>
                    <ArrowLeft size={20} />
                    Voltar para Simulados
                </button>
                <h2>Desempenho: Prova {simulado.prova}</h2>
            </header>

            <div className={styles['performance__score-card']}>
                <div className={styles['score-item']}>
                    <h3>Nota Final</h3>
                    <div className={styles.value}>{scorePercent}%</div>
                </div>
                <div className={styles['score-item']}>
                    <h3>Acertos</h3>
                    <div className={cn(styles.value, styles.correct)}>{correctCount}</div>
                </div>
                <div className={styles['score-item']}>
                    <h3>Erros</h3>
                    <div className={cn(styles.value, styles.incorrect)}>{total - correctCount}</div>
                </div>
            </div>

            <div className={styles.performance__questions}>
                {questions.map((question, index) => {
                    const userAnswer = question.resposta_usuario?.toUpperCase() ?? null;
                    const gabarito = question.gabarito || parseGabaritoFromSolucao(question.solucao);
                    const isCorrect = userAnswer === gabarito;
                    const parsed = parseQuestaoForDisplay(question.enunciado, question.alternativas);
                    const isChatOpen = openChats[question.id];

                    return (
                        <div key={question.id} className={styles['performance__question-card']}>
                            <div className={styles.header}>
                                <h3>Questão {index + 1}</h3>
                                <span
                                    className={cn(
                                        styles.status,
                                        isCorrect ? styles.correct : styles.incorrect
                                    )}
                                >
                                    {isCorrect ? 'Correta' : 'Incorreta'}
                                </span>
                            </div>

                            <div className={styles.body}>
                                <div className={styles.statement}>
                                    {renderLatexContent(parsed.statement)}
                                </div>

                                <div className={styles.alternatives}>
                                    {parsed.alternatives.map((alt) => {
                                        const isSelected = userAnswer === alt.label;
                                        const isTheCorrectOne = gabarito === alt.label;

                                        let className = styles.alternative;
                                        if (isTheCorrectOne)
                                            className = cn(className, styles.correct);
                                        else if (isSelected && !isCorrect)
                                            className = cn(className, styles['selected-incorrect']);

                                        return (
                                            <div key={alt.label} className={className}>
                                                <span className={styles.label}>{alt.label}</span>
                                                <span className={styles.value}>
                                                    {renderLatexContent(alt.text)}
                                                </span>
                                                {isTheCorrectOne && (
                                                    <span
                                                        style={{
                                                            marginLeft: 'auto',
                                                            fontSize: '0.8rem',
                                                            color: '#10b981',
                                                        }}
                                                    >
                                                        Gabarito
                                                    </span>
                                                )}
                                                {isSelected && !isCorrect && (
                                                    <span
                                                        style={{
                                                            marginLeft: 'auto',
                                                            fontSize: '0.8rem',
                                                            color: '#ef4444',
                                                        }}
                                                    >
                                                        Sua resposta
                                                    </span>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>

                                <div className={styles['chat-section']}>
                                    {(isChatOpen || closingChatId === question.id) ? (
                                        <div
                                            className={cn(
                                                styles['chat-expanded'],
                                                closingChatId === question.id && styles['chat-expanded--closing'],
                                                openingChatId === question.id && styles['chat-expanded--opening']
                                            )}
                                            onTransitionEnd={
                                                closingChatId === question.id
                                                    ? handleChatCloseAnimationEnd
                                                    : undefined
                                            }
                                        >
                                            <div className={styles['chat-expanded-header']}>
                                                <span>Tutor IA - Questão {index + 1}</span>
                                                <button
                                                    type="button"
                                                    className={styles['chat-expanded-collapse']}
                                                    onClick={() => startCloseChat(question.id)}
                                                    title="Recolher chat"
                                                    disabled={closingChatId === question.id}
                                                >
                                                    <ChevronUp size={18} />
                                                </button>
                                            </div>
                                            <div className={styles['chat-expanded-chat']}>
                                                <QuestionChat
                                                    simuladoId={id!}
                                                    questionId={question.id}
                                                    fullScreen
                                                />
                                            </div>
                                        </div>
                                    ) : (
                                        <button
                                            type="button"
                                            className={styles['chat-toggle']}
                                            onClick={() => startOpenChat(question.id)}
                                        >
                                            <div className={styles.title}>
                                                <Bot size={18} />
                                                Tutor IA - Tire suas dúvidas
                                            </div>
                                            <ChevronDown size={18} />
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
