import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, ChevronDown, Sparkles } from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';
import 'katex/dist/katex.min.css';
import styles from './Chat.module.scss';
import { type Message } from '../../mockData';
import { cn } from '../../lib/utils';
import API from '../../services/api';
import { useChat } from '../../contexts/ChatContext';
import { QuestionCard } from '../../components/QuestionCard';

import { renderMessage } from "../../lib/utils"

type ContentItem = { type?: string; content?: string; language?: string }

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
                case 'code':
                    return `\`\`\`${item.language ?? ''}\n${content}\n\`\`\`\n\n`;
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

export const Chat: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { triggerRefreshHistory } = useChat();
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    const messagesContainerRef = useRef<HTMLDivElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const lastUserMessageRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
        messagesEndRef.current?.scrollIntoView({ behavior });
    };

    const scrollToLastUserMessage = (behavior: ScrollBehavior = "smooth") => {
        if (lastUserMessageRef.current) {
            lastUserMessageRef.current.scrollIntoView({ behavior, block: 'start' });
        } else {
            scrollToBottom(behavior);
        }
    };

    const handleScroll = () => {
        if (!messagesContainerRef.current) return;
        const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
        const isNearBottom = scrollHeight - scrollTop - clientHeight < 200;
        setShowScrollButton(!isNearBottom);
    };

    // When messages change: scroll to the last user message so the question is at the top
    useEffect(() => {
        if (messages.length === 0) return;
        const lastMsg = messages[messages.length - 1];
        if (lastMsg.role === 'user') {
            // User just sent a message — scroll their message to top
            setTimeout(() => scrollToLastUserMessage('smooth'), 50);
        } else if (lastMsg.role === 'assistant') {
            // Bot responded — scroll the preceding user question to top
            setTimeout(() => scrollToLastUserMessage('smooth'), 50);
        }
    }, [messages]);

    // While loading (typing indicator), keep the user question at top
    useEffect(() => {
        if (isLoading) {
            setTimeout(() => scrollToLastUserMessage('smooth'), 50);
        }
    }, [isLoading]);

    useEffect(() => {
        if (id && id !== 'new') {
            const fetchMessages = async () => {
                try {
                    const response = await API.get(`/api/chat/${id}/`);
                    setMessages(response.data);
                } catch (error) {
                    console.error('Error fetching messages:', error);
                }
            };
            fetchMessages();
        } else {
            setMessages([]);
        }
        inputRef.current?.focus();
    }, [id]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const payload: any = { message: input };
            if (id && id !== 'new') {
                payload.session_id = id;
            }

            const response = await API.post('/api/chat/', payload);

            if (response.data?.status === 'success') {
                const data = response.data?.data;
                const items = data?.items;
                const formattedFromBackend = typeof data?.formatted_content === 'string' ? data.formatted_content : '';
                const contentFromItems = formatItemsToContent(items);
                const botContent = (formattedFromBackend || contentFromItems).trim();

                const questionData = data?.question_data;

                const botMessage: Message = {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: botContent,
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    ...(questionData != null && { question_data: questionData })
                };

                setMessages(prev => [...prev, botMessage]);
                inputRef.current?.focus();

                if (id === 'new' && response.data.session_id) {
                    triggerRefreshHistory();
                    navigate(`/chat/${response.data.session_id}`, { replace: true });
                }
            }
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                isError: true,
                content: 'Ops! Ocorreu um probleminha ao processar sua dúvida. Por favor, tente novamente em instantes.',
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={styles.chat}>
            <div
                className={styles.chat__messages}
                ref={messagesContainerRef}
                onScroll={handleScroll}
            >
                {messages.length === 0 && id === 'new' ? (
                    <div className={styles.chat__welcome}>
                        <h2>Bem-vindo ao TutorPE!</h2>
                        <p>Estou aqui para ajudar você com Probabilidade e Estatística.</p>
                        <div className={styles.chat__suggestions}>
                            <button onClick={() => setInput("Como calcular a média?")}>
                                <Sparkles size={14} className={styles.sparkle} /> Como calcular a média?
                            </button>
                            <button onClick={() => setInput("O que é desvio padrão?")}>
                                <Sparkles size={14} className={styles.sparkle} /> O que é desvio padrão?
                            </button>
                            <button onClick={() => setInput("Explique o Teorema de Bayes")}>
                                <Sparkles size={14} className={styles.sparkle} /> Explique o Teorema de Bayes
                            </button>
                        </div>
                    </div>
                ) : (
                    messages.map((msg, index) => {
                        // Find last user message index
                        const lastUserIndex = messages.reduce((acc, m, i) => m.role === 'user' ? i : acc, -1);
                        const isLastUserMessage = msg.role === 'user' && index === lastUserIndex;

                        return (
                            <div
                                key={msg.id}
                                ref={isLastUserMessage ? lastUserMessageRef : undefined}
                                className={cn(
                                    styles.chat__message,
                                    styles[msg.role],
                                    msg.isError && styles.error,
                                    msg.question_data && styles.has_card
                                )}
                            >
                                <div className={cn(styles.chat__avatar, msg.role === 'assistant' ? styles.bot : styles.user)}>
                                    {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
                                </div>
                                <div className={styles.chat__bubble}>
                                    {msg.role === 'assistant' && msg.question_data && (
                                        <div className={styles.message_question_card}>
                                            <QuestionCard data={msg.question_data} />
                                        </div>
                                    )}
                                    <div className={styles.message_text}>
                                        {renderMessage(msg.content)}
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
                {isLoading && (
                    <div className={cn(styles.chat__message, styles.assistant, styles.loading)}>
                        <div className={cn(styles.chat__avatar, styles.bot)}>
                            <Bot size={20} />
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
                <div ref={messagesEndRef} />
            </div>

            {showScrollButton && (
                <button
                    className={styles.chat__scroll_btn}
                    onClick={() => scrollToBottom("smooth")}
                    aria-label="Rolar para baixo"
                >
                    <ChevronDown size={20} />
                </button>
            )}

            <div className={styles['chat__input-container']}>
                <textarea
                    ref={inputRef}
                    className={styles.chat__input}
                    placeholder="Digite sua pergunta sobre Probabilidade e Estatística..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSend();
                        }
                    }}
                    rows={1}
                    disabled={isLoading}
                />
                <button
                    className={cn(styles['chat__action-btn'], styles.send)}
                    onClick={handleSend}
                    disabled={isLoading || !input.trim()}
                >
                    <Send size={20} />
                </button>
            </div>
        </div>
    );
};
