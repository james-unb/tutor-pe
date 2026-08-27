import React, { useState, useEffect } from 'react';
import { Send, Bot, User } from 'lucide-react';
import 'katex/dist/katex.min.css';
import styles from './QuestionChat.module.scss';
import { cn } from '../lib/utils';
import type { Message } from '../mockData';
import { renderMessage } from '../lib/utils';
import {
    getSimuladoChatMessages,
    sendSimuladoChatMessage,
} from '../services/simuladosApi';

type ContentItem = { type?: string; content?: string };

function formatItemsToContent(items: ContentItem[] | undefined): string {
    if (!items || !Array.isArray(items)) return '';
    return items
        .map((item) => {
            const content = item.content ?? '';
            switch (item.type) {
                case 'title':
                    return `**${content}**\n\n`;
                case 'subtitle':
                    return `<h3>${content}</h3>\n\n`;
                case 'formula':
                    return `$$${content}$$\n\n`;
                case 'list_item':
                    return `- ${content}\n`;
                case 'table':
                    return content;
                default:
                    return `${content}\n\n`;
            }
        })
        .join('');
}

interface QuestionChatProps {
    simuladoId: string;
    questionId: string;
    /** Quando true, o chat ocupa 100% da altura do container (ex.: overlay em tela cheia) */
    fullScreen?: boolean;
}

export const QuestionChat: React.FC<QuestionChatProps> = ({
    simuladoId,
    questionId,
    fullScreen = false,
}) => {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [loadingHistory, setLoadingHistory] = useState(true);

    useEffect(() => {
        if (!simuladoId || !questionId) return;
        setLoadingHistory(true);
        getSimuladoChatMessages(simuladoId, questionId)
            .then((list) => {
                setMessages(
                    list.map((m) => ({
                        id: m.id,
                        role: m.role,
                        content: m.content,
                        timestamp: m.timestamp,
                    }))
                );
            })
            .catch(() => {
                setMessages([]);
            })
            .finally(() => setLoadingHistory(false));
    }, [simuladoId, questionId]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMsg: Message = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: input.trim(),
            timestamp: new Date().toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
            }),
        };
        setMessages((prev) => [...prev, userMsg]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await sendSimuladoChatMessage(
                simuladoId,
                questionId,
                input.trim()
            );
            if (response?.status === 'success' && response?.data) {
                const formattedFromBackend =
                    typeof response.data.formatted_content === 'string'
                        ? response.data.formatted_content
                        : '';
                const contentFromItems = formatItemsToContent(
                    response.data.items
                );
                const botContent = (
                    formattedFromBackend || contentFromItems
                ).trim();
                const botMsg: Message = {
                    id: `assistant-${Date.now()}`,
                    role: 'assistant',
                    content: botContent,
                    timestamp: new Date().toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                    }),
                };
                setMessages((prev) => [...prev, botMsg]);
            }
        } catch {
            const errorMsg: Message = {
                id: `error-${Date.now()}`,
                role: 'assistant',
                content:
                    'Não foi possível enviar. Tente novamente em instantes.',
                timestamp: new Date().toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                }),
                isError: true,
            };
            setMessages((prev) => [...prev, errorMsg]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={cn(styles.chat, fullScreen && styles.chatFullScreen)}>
            <div className={styles.chat__messages}>
                {loadingHistory ? (
                    <div className={cn(styles.chat__message, styles.assistant)}>
                        <div
                            className={cn(
                                styles.chat__avatar,
                                styles.bot
                            )}
                        >
                            <Bot size={16} />
                        </div>
                        <div className={styles.chat__bubble}>
                            Carregando conversa...
                        </div>
                    </div>
                ) : messages.length === 0 ? (
                    <div className={cn(styles.chat__message, styles.assistant)}>
                        <div
                            className={cn(
                                styles.chat__avatar,
                                styles.bot
                            )}
                        >
                            <Bot size={16} />
                        </div>
                        <div className={styles.chat__bubble}>
                            Olá! Ficou com alguma dúvida nesta questão? Posso
                            explicar a solução passo a passo.
                        </div>
                    </div>
                ) : (
                    messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={cn(
                                styles.chat__message,
                                styles[msg.role],
                                msg.isError && styles.error
                            )}
                        >
                            <div
                                className={cn(
                                    styles.chat__avatar,
                                    msg.role === 'assistant'
                                        ? styles.bot
                                        : styles.user
                                )}
                            >
                                {msg.role === 'assistant' ? (
                                    <Bot size={16} />
                                ) : (
                                    <User size={16} />
                                )}
                            </div>
                            <div className={styles.chat__bubble}>
                                {renderMessage(msg.content)}
                            </div>
                        </div>
                    ))
                )}
                {isLoading && (
                    <div
                        className={cn(
                            styles.chat__message,
                            styles.assistant
                        )}
                    >
                        <div
                            className={cn(
                                styles.chat__avatar,
                                styles.bot
                            )}
                        >
                            <Bot size={16} />
                        </div>
                        <div className={styles.chat__bubble}>
                            <div className={styles.typing}>
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <div className={styles['chat__input-container']}>
                <input
                    className={styles.chat__input}
                    placeholder="Tire suas dúvidas..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) =>
                        e.key === 'Enter' && !e.shiftKey && handleSend()
                    }
                    disabled={isLoading || loadingHistory}
                />
                <button
                    className={styles['chat__send-btn']}
                    onClick={handleSend}
                    disabled={
                        !input.trim() || isLoading || loadingHistory
                    }
                >
                    <Send size={16} />
                </button>
            </div>
        </div>
    );
};
