import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, CheckCircle, BarChart, Clock, MessageSquarePlus } from 'lucide-react';
import styles from './Simulados.module.scss';
import { cn } from '../../lib/utils';
import { CreateSimuladoModal } from '../../components/CreateSimuladoModal';
import { listSimulados, createSimulado } from '../../services/simuladosApi';
import type { SimuladoFromApi } from '../../types/simulado';

type SimuladoStatus = 'completed' | 'in_progress' | 'not_started';

function formatDate(createdAt: string): string {
    try {
        const d = new Date(createdAt);
        return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    } catch {
        return '';
    }
}

function formatTimeSpent(seconds: number | null): string {
    if (seconds == null) return '—';
    const min = Math.floor(seconds / 60);
    if (min < 60) return `${min} min`;
    const h = Math.floor(min / 60);
    const m = min % 60;
    return m ? `${h}h ${m}min` : `${h}h`;
}

export const Simulados: React.FC = () => {
    const navigate = useNavigate();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [simulados, setSimulados] = useState<SimuladoFromApi[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [creating, setCreating] = useState(false);

    const fetchList = () => {
        setLoading(true);
        setError(null);
        listSimulados()
            .then(setSimulados)
            .catch((err) => {
                const msg = err.response?.data?.error ?? err.message ?? 'Erro ao carregar simulados.';
                setError(msg);
                setSimulados([]);
            })
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        fetchList();
    }, []);

    const handleStart = (id: string) => {
        navigate(`/simulados/${id}/play`);
    };

    const handlePerformance = (id: string) => {
        navigate(`/simulados/${id}/performance`);
    };

    const handleCreateSimulado = async (_name: string, examId: string) => {
        setCreating(true);
        try {
            const data = await createSimulado(Number(examId));
            setCreating(false);
            navigate(`/simulados/${data.id}/play`);
        } catch (err: unknown) {
            setCreating(false);
            const msg =
                (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
                (err as Error)?.message ??
                'Erro ao criar simulado.';
            alert(msg);
        }
    };

    const concluidos = simulados.filter((s) => s.concluido);
    const simuladosConcluidosCount = concluidos.length;
    const taxaAcertos =
        concluidos.length > 0
            ? Math.round(
                  (concluidos.reduce((acc, s) => acc + (s.nota ?? 0), 0) / concluidos.length) * 10
              )
            : 0;
    const tempoMedioSegundos =
        concluidos.length > 0
            ? Math.round(
                  concluidos.reduce((acc, s) => acc + (s.tempo_segundos ?? 0), 0) / concluidos.length
              )
            : 0;

    const getStatus = (s: SimuladoFromApi): SimuladoStatus =>
        s.concluido ? 'completed' : 'in_progress';

    return (
        <div className={styles.simulados}>
            <header className={styles.simulados__header}>
                <h1>Simulados</h1>
                <button onClick={() => setIsModalOpen(true)} disabled={creating}>
                    <Plus size={20} />
                    Criar novo simulado
                </button>
            </header>

            <div className={styles.simulados__stats}>
                <div className={styles['simulados__stats-card']}>
                    <div className={cn(styles['simulados__stats-card-icon'], styles.completed)}>
                        <CheckCircle size={24} />
                    </div>
                    <div className={styles['simulados__stats-card-info']}>
                        <h3>Simulados Concluídos</h3>
                        <p>{loading ? '—' : simuladosConcluidosCount}</p>
                    </div>
                </div>
                <div className={styles['simulados__stats-card']}>
                    <div className={cn(styles['simulados__stats-card-icon'], styles.accuracy)}>
                        <BarChart size={24} />
                    </div>
                    <div className={styles['simulados__stats-card-info']}>
                        <h3>Taxa de Acertos</h3>
                        <p>{loading ? '—' : `${taxaAcertos}%`}</p>
                    </div>
                </div>
                <div className={styles['simulados__stats-card']}>
                    <div className={cn(styles['simulados__stats-card-icon'], styles.time)}>
                        <Clock size={24} />
                    </div>
                    <div className={styles['simulados__stats-card-info']}>
                        <h3>Tempo Médio</h3>
                        <p>{loading ? '—' : formatTimeSpent(tempoMedioSegundos)}</p>
                    </div>
                </div>
            </div>

            {error && (
                <div className={styles.simulados__error}>
                    {error}
                    <button type="button" onClick={fetchList}>
                        Tentar novamente
                    </button>
                </div>
            )}

            {loading ? (
                <div className={styles.simulados__loading}>Carregando simulados...</div>
            ) : simulados.length === 0 ? (
                <div className={styles.simulados__empty}>
                    <p>Você ainda não tem nenhum simulado.</p>
                    <p className={styles.simulados__emptyHint}>
                        Crie um simulado para praticar ou inicie um chat com o tutor.
                    </p>
                    <div className={styles.simulados__emptyActions}>
                        <button
                            type="button"
                            className={cn(styles.simulados__emptyBtn, styles.simulados__emptyBtnPrimary)}
                            onClick={() => setIsModalOpen(true)}
                        >
                            <Plus size={20} />
                            Criar novo simulado
                        </button>
                        <button
                            type="button"
                            className={styles.simulados__emptyBtn}
                            onClick={() => navigate('/chat/new')}
                        >
                            <MessageSquarePlus size={20} />
                            Iniciar chat
                        </button>
                    </div>
                </div>
            ) : (
                <div className={styles.simulados__grid}>
                    {simulados.map((simulado) => {
                        const status = getStatus(simulado);
                        return (
                            <div key={simulado.id} className={styles.simulados__card}>
                                <div className={styles['simulados__card-header']}>
                                    <div>
                                        <h3>Prova {simulado.prova} – {formatDate(simulado.created_at)}</h3>
                                        <span>Dificuldade média: {simulado.dificuldade_media.toFixed(1)}</span>
                                    </div>
                                    <span className={cn(styles['simulados__card-badge'], styles[status])}>
                                        {status === 'in_progress'
                                            ? 'Em andamento'
                                            : status === 'completed'
                                              ? 'Concluído'
                                              : 'Não iniciado'}
                                    </span>
                                </div>

                                <div className={styles['simulados__card-info']}>
                                    <span>10 questões</span>
                                    {simulado.tempo_segundos != null && (
                                        <span>{formatTimeSpent(simulado.tempo_segundos)}</span>
                                    )}
                                </div>

                                <button
                                    className={cn(
                                        styles['simulados__card-action'],
                                        status === 'completed' ? styles.secondary : styles.primary
                                    )}
                                    onClick={() =>
                                        status === 'completed'
                                            ? handlePerformance(simulado.id)
                                            : handleStart(simulado.id)
                                    }
                                >
                                    {status === 'completed'
                                        ? 'Ver desempenho'
                                        : status === 'in_progress'
                                          ? 'Continuar'
                                          : 'Iniciar'}
                                </button>
                            </div>
                        );
                    })}
                </div>
            )}

            <CreateSimuladoModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onCreate={handleCreateSimulado}
            />
        </div>
    );
};
