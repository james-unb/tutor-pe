import React, { createContext, useState, useContext, type ReactNode, useCallback } from 'react';

interface ChatContextType {
    shouldRefreshHistory: boolean;
    triggerRefreshHistory: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [shouldRefreshHistory, setShouldRefreshHistory] = useState(false);

    const triggerRefreshHistory = useCallback(() => {
        setShouldRefreshHistory(prev => !prev);
    }, []);

    return (
        <ChatContext.Provider value={{ shouldRefreshHistory, triggerRefreshHistory }}>
            {children}
        </ChatContext.Provider>
    );
};

export const useChat = () => {
    const context = useContext(ChatContext);
    if (!context) {
        throw new Error('useChat must be used within a ChatProvider');
    }
    return context;
};
