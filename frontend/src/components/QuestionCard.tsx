import React from 'react';
import styles from './QuestionCard.module.scss';
import 'katex/dist/katex.min.css';
import { renderLatexContent } from '../lib/utils';

interface Item {
    codigo: string;
    enunciado: string;
}

interface QuestionData {
    id: string;
    number: number;
    assignment: number;
    enunciado: string;
    itens: Item[];
}

interface QuestionCardProps {
    data: QuestionData;
}

const renderText = (text: string) => renderLatexContent(text, { tableWrapper: styles.tableWrapper });

export const QuestionCard: React.FC<QuestionCardProps> = ({ data }) => {
    return (
        <div className={styles.card}>
            <div className={styles.header}>
                <h3>Questão {data.number}</h3>
                <span className={styles.badge}>Lista {data.assignment}</span>
            </div>
            <div className={styles.body}>
                <p>{renderText(data.enunciado)}</p>
            </div>
            {data.itens && data.itens.length > 0 && (
                <div className={styles.items}>
                    {data.itens.map((item, index) => (
                        <div key={index} className={styles.item}>
                            <span className={styles.label}>{item.codigo}</span>
                            <span className={styles.text}>{renderText(item.enunciado)}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
