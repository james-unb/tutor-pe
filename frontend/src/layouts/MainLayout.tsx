import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import styles from './MainLayout.module.scss';
import { useContext } from 'react';
import AuthContext from '../contexts/AuthContext';
import { cn } from '../lib/utils';
import { ChatProvider } from '../contexts/ChatContext';

export const MainLayout: React.FC = () => {

    const { isAuthenticated } = useContext(AuthContext);
    const location = useLocation();
    const isChat = location.pathname.startsWith('/chat');
    const [isPinned, setIsPinned] = React.useState(() => {
        const saved = localStorage.getItem('sidebarPinned');
        return saved !== null ? saved === 'true' : true;
    });

    const togglePin = () => {
        setIsPinned((prev) => {
            const newState = !prev;
            localStorage.setItem('sidebarPinned', String(newState));
            return newState;
        });
    };

    if (!isAuthenticated) {
        return <Navigate to="/login" />;
    }
    return (
        <ChatProvider>
            <div className={cn(styles.layout, !isPinned && styles.unpinned)}>
                <Sidebar isPinned={isPinned} togglePin={togglePin} />
                <main className={cn(styles.layout__content, isChat && styles.chatMode)}>
                    <Outlet />
                </main>
            </div>
        </ChatProvider>
    );
};
