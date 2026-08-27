import React, { useEffect, useState, useContext } from 'react';
import { NavLink } from 'react-router-dom';
import { MessageSquarePlus, LogOut, LayoutDashboard, MessageSquare, PanelLeftClose, PanelLeftOpen, Clock, Sun, Moon, Settings } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import styles from './Sidebar.module.scss';
import { type ChatSession } from '../mockData';
import { cn } from '../lib/utils';
import { Logo } from './Logo';
import AuthContext from '../contexts/AuthContext';
import API from '../services/api';
import { useChat } from '../contexts/ChatContext';

interface SidebarProps {
    isPinned: boolean;
    togglePin: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isPinned, togglePin }) => {
    const { signOut } = useContext(AuthContext);
    const { theme, toggleTheme } = useTheme();
    const { shouldRefreshHistory } = useChat();
    const [chats, setChats] = useState<ChatSession[]>([]);
    const [mobileHistoryOpen, setMobileHistoryOpen] = useState(false);
    const [mobileSettingsOpen, setMobileSettingsOpen] = useState(false);

    useEffect(() => {
        const fetchChats = async () => {
            try {
                const response = await API.get('/api/chat/history/');
                setChats(response.data);
            } catch (error) {
                console.error('Error fetching chats:', error);
            }
        };

        fetchChats();
    }, [shouldRefreshHistory]);

    return (
        <aside
            className={cn(
                styles.sidebar,
                !isPinned && styles.unpinned
            )}
        >
            <div className={styles.sidebar__header}>
                <NavLink to="/simulados" className={styles.sidebar__logo}>
                    <Logo />
                    <span>TutorPE</span>
                </NavLink>
            </div>

            <nav className={styles.sidebar__nav}>
                <NavLink
                    to="/simulados"
                    className={({ isActive }) => cn(styles.sidebar__link, isActive && styles.active)}
                >
                    <LayoutDashboard size={20} />
                    <span>Simulados</span>
                </NavLink>
                <NavLink
                    to="/chat/new"
                    className={({ isActive }) => cn(styles.sidebar__link, isActive && styles.active)}
                >
                    <MessageSquarePlus size={20} />
                    <span>Novo Chat</span>
                </NavLink>
            </nav>

            {/* Mobile-only history toggle */}
            <button
                className={cn(styles.sidebar__link, styles['sidebar__history-toggle-mobile'])}
                onClick={() => setMobileHistoryOpen((prev) => !prev)}
            >
                <Clock size={20} />
                <span>Histórico</span>
            </button>

            <div className={styles.sidebar__history}>
                <div className={styles['sidebar__history-title']}>
                    <Clock size={20} />
                    <span>Chats Recentes</span>
                </div>
                <div className={styles['sidebar__history-list']}>
                    {chats.map((chat) => (
                        <NavLink
                            key={chat.id}
                            to={`/chat/${chat.id}`}
                            className={({ isActive }) => cn(styles['sidebar__history-item'], isActive && styles.active)}
                        >
                            <MessageSquare size={16} />
                            <span>{chat.title || 'Sem título'}</span>
                        </NavLink>
                    ))}
                </div>
            </div>

            <div className={styles.sidebar__bottom}>
                {/* Desktop: show individual buttons */}
                <button
                    onClick={toggleTheme}
                    className={cn(styles.sidebar__link, styles['sidebar__toggle-bottom'])}
                    title={theme === 'dark' ? 'Tema claro' : 'Tema escuro'}
                >
                    {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                    <span>{theme === 'dark' ? 'Claro' : 'Escuro'}</span>
                </button>
                <button onClick={signOut} className={cn(styles.sidebar__link, styles['sidebar__toggle-bottom'])}>
                    <LogOut size={20} />
                    <span>Sair</span>
                </button>
                <button
                    onClick={togglePin}
                    className={cn(styles.sidebar__link, styles['sidebar__toggle-bottom'])}
                    title={isPinned ? "Desafixar menu" : "Fixar menu aberto"}
                >
                    {isPinned ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
                    <span>{isPinned ? "Desafixar" : "Fixar"}</span>
                </button>

                {/* Mobile: single settings button with popup */}
                <div className={styles['sidebar__settings-mobile']}>
                    <button
                        className={styles.sidebar__link}
                        onClick={() => setMobileSettingsOpen(prev => !prev)}
                    >
                        <Settings size={20} />
                    </button>
                    {mobileSettingsOpen && (
                        <>
                            <div
                                className={styles['sidebar__settings-overlay']}
                                onClick={() => setMobileSettingsOpen(false)}
                            />
                            <div className={styles['sidebar__settings-popup']}>
                                <button
                                    onClick={() => { toggleTheme(); setMobileSettingsOpen(false); }}
                                    className={styles['sidebar__settings-item']}
                                >
                                    {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                                    <span>{theme === 'dark' ? 'Tema Claro' : 'Tema Escuro'}</span>
                                </button>
                                <button
                                    onClick={() => { signOut(); setMobileSettingsOpen(false); }}
                                    className={cn(styles['sidebar__settings-item'], styles['sidebar__settings-item--danger'])}
                                >
                                    <LogOut size={18} />
                                    <span>Sair da Conta</span>
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* Mobile history drawer */}
            {mobileHistoryOpen && (
                <div className={styles.sidebar__mobileOverlay} onClick={() => setMobileHistoryOpen(false)} />
            )}
            <div className={cn(styles.sidebar__mobileHistory, mobileHistoryOpen && styles.open)}>
                <div className={styles['sidebar__mobileHistory-header']}>
                    <span>Chats Recentes</span>
                    <button onClick={() => setMobileHistoryOpen(false)}>&times;</button>
                </div>
                <div className={styles['sidebar__mobileHistory-list']}>
                    {chats.length === 0 ? (
                        <p className={styles['sidebar__mobileHistory-empty']}>Nenhum chat ainda</p>
                    ) : (
                        chats.map((chat) => (
                            <NavLink
                                key={chat.id}
                                to={`/chat/${chat.id}`}
                                className={({ isActive }) => cn(styles['sidebar__mobileHistory-item'], isActive && styles.active)}
                                onClick={() => setMobileHistoryOpen(false)}
                            >
                                <MessageSquare size={16} />
                                <span>{chat.title || 'Sem título'}</span>
                            </NavLink>
                        ))
                    )}
                </div>
            </div>
        </aside>
    );
};
