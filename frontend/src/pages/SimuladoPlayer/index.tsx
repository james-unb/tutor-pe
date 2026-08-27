import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, CheckCircle, Clock } from 'lucide-react';
import 'katex/dist/katex.min.css';
import styles from './SimuladoPlayer.module.scss';
import { cn, renderLatexContent } from '../../lib/utils';
import { getSimulado, getQuestoes, submitResposta, finalizarSimulado } from '../../services/simuladosApi';
import type { SimuladoFromApi, QuestaoFromApi } from '../../types/simulado';
import { parseQuestaoForDisplay } from '../../lib/parseEnunciado';

function formatTimer(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

export const SimuladoPlayer: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [simulado, setSimulado] = useState<SimuladoFromApi | null>(null);
    const [questions, setQuestions] = useState<QuestaoFromApi[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [answers, setAnswers] = useState<Record<string, string>>({});
    const [timerSeconds, setTimerSeconds] = useState(0);
    const [finalizing, setFinalizing] = useState(false);

    useEffect(() => {
        if (!id) return;
        setLoading(true);
        setError(null);
        Promise.all([getSimulado(id), getQuestoes(id)])
            .then(([sim, qs]) => {
                setSimulado(sim);
                setQuestions(qs);
                const initial: Record<string, string> = {};
                qs.forEach((q) => {
                    if (q.resposta_usuario) {
                        initial[q.id] = q.resposta_usuario.toUpperCase();
                    }
                });
                setAnswers(initial);
            })
            .catch((err) => {
                const msg = err.response?.data?.error ?? err.message ?? 'Erro ao carregar simulado.';
                setError(msg);
            })
            .finally(() => setLoading(false));
    }, [id]);

    useEffect(() => {
        if (!simulado || simulado.concluido) return;
        const interval = setInterval(() => setTimerSeconds((s) => s + 1), 1000);
        return () => clearInterval(interval);
    }, [simulado]);

    const handleSelect = useCallback(
        (questionId: string, label: string) => {
            if (!id) return;
            setAnswers((prev) => ({ ...prev, [questionId]: label }));
            submitResposta(id, questionId, label).catch(() => {
                // could show toast; answer is still in local state
            });
        },
        [id]
    );

    const handleNext = () => {
        const isLastQuestion = currentQuestionIndex === questions.length - 1;
        if (isLastQuestion) {
            setFinalizing(true);
            finalizarSimulado(id!, timerSeconds)
                .then(() => {
                    navigate(`/simulados/${id}/performance`);
                })
                .catch((err) => {
                    setFinalizing(false);
                    const msg =
                        err.response?.data?.error ?? err.message ?? 'Erro ao finalizar simulado.';
                    alert(msg);
                });
        } else {
            setCurrentQuestionIndex((prev) => prev + 1);
        }
    };

    const handlePrev = () => {
        if (currentQuestionIndex > 0) {
            setCurrentQuestionIndex((prev) => prev - 1);
        }
    };

    if (loading) {
        return (
            <div className={styles.player}>
                <div className={styles.player__loading}>Carregando...</div>
            </div>
        );
    }
    if (error || !simulado) {
        return (
            <div className={styles.player}>
                <div className={styles.player__error}>{error ?? 'Simulado não encontrado.'}</div>
            </div>
        );
    }
    if (simulado.concluido) {
        navigate(`/simulados/${id}/performance`, { replace: true });
        return null;
    }
    if (questions.length === 0) {
        return (
            <div className={styles.player}>
                <div className={styles.player__error}>Este simulado ainda não tem questões.</div>
            </div>
        );
    }

    const currentQuestion = questions[currentQuestionIndex];
    const parsed = parseQuestaoForDisplay(currentQuestion.enunciado, currentQuestion.alternativas);
    const isLastQuestion = currentQuestionIndex === questions.length - 1;
    const isFirstQuestion = currentQuestionIndex === 0;

    return (
        <div className={styles.player}>
            <header className={styles.player__header}>
                <div>
                    <h2>Prova {simulado.prova}</h2>
                    <span style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
                        {questions.length} questões
                    </span>
                </div>
                <div className={styles.timer}>
                    <Clock size={20} />
                    <span>{formatTimer(timerSeconds)}</span>
                </div>
            </header>

            <div className={styles.player__content}>
                <div className={styles.player__question}>
                    <h3>
                        Questão {currentQuestionIndex + 1} de {questions.length}
                    </h3>
                    <div className={styles.statement}>{renderLatexContent(parsed.statement)}</div>
                </div>

                <div className={styles.player__alternatives}>
                    {parsed.alternatives.map((alt) => (
                        <div
                            key={alt.label}
                            className={cn(
                                styles.player__option,
                                answers[currentQuestion.id] === alt.label && styles.selected
                            )}
                            onClick={() => handleSelect(currentQuestion.id, alt.label)}
                        >
                            <div className={styles.radio} />
                            <span className={styles.label}>{alt.label}</span>
                            <span className={styles.value}>{renderLatexContent(alt.text)}</span>
                        </div>
                    ))}
                </div>
            </div>

            <footer className={styles.player__footer}>
                <button
                    className={styles.prev}
                    onClick={handlePrev}
                    disabled={isFirstQuestion}
                >
                    <ChevronLeft size={20} />
                    Anterior
                </button>
                <button
                    className={styles.next}
                    onClick={handleNext}
                    disabled={finalizing}
                >
                    {isLastQuestion ? 'Finalizar' : 'Próxima'}
                    {!isLastQuestion && <ChevronRight size={20} />}
                    {isLastQuestion && <CheckCircle size={20} />}
                </button>
            </footer>
        </div>
    );
};
