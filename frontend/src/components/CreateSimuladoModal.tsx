import React, { useState } from 'react';
import { X } from 'lucide-react';
import styles from './CreateSimuladoModal.module.scss';

const PROVAS = [
    { value: '1', title: 'Prova 1' },
    { value: '2', title: 'Prova 2' },
    { value: '3', title: 'Prova 3' },
];

interface CreateSimuladoModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreate: (name: string, examId: string) => void;
}

export const CreateSimuladoModal: React.FC<CreateSimuladoModalProps> = ({ isOpen, onClose, onCreate }) => {
    const [selectedExam, setSelectedExam] = useState<string>('');
    const [name, setName] = useState<string>('');

    if (!isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (selectedExam && name.trim()) {
            onCreate(name, selectedExam);
            onClose();
            setSelectedExam('');
            setName('');
        }
    };

    return (
        <div className={styles.overlay}>
            <div className={styles.modal}>
                <header className={styles.header}>
                    <h2>Novo Simulado</h2>
                    <button onClick={onClose} className={styles.closeButton}>
                        <X size={24} />
                    </button>
                </header>

                <form onSubmit={handleSubmit}>
                    <div className={styles.content}>
                        <div className={styles.field}>
                            <label htmlFor="simulado-name">Nome do Simulado:</label>
                            <input
                                id="simulado-name"
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Ex: Simulado P1"
                                required
                            />
                        </div>

                        <div className={styles.field}>
                            <label htmlFor="exam-select">Selecione a prova base:</label>
                            <select
                                id="exam-select"
                                value={selectedExam}
                                onChange={(e) => setSelectedExam(e.target.value)}
                                required
                            >
                                <option value="" disabled>Selecione uma prova...</option>
                                {PROVAS.map((exam) => (
                                    <option key={exam.value} value={exam.value}>
                                        {exam.title}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <footer className={styles.footer}>
                        <button type="button" onClick={onClose} className={styles.cancelButton}>
                            Cancelar
                        </button>
                        <button type="submit" className={styles.createButton} disabled={!selectedExam || !name.trim()}>
                            Criar Simulado
                        </button>
                    </footer>
                </form>
            </div>
        </div>
    );
};
