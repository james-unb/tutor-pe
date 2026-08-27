import { createContext, useEffect, useState } from "react";

interface AuthContextProps {
    children: React.ReactNode
}

interface AuthContextType {
    signIn: (jwtToken: string) => void
    signOut: () => void
    isAuthenticated: boolean
}

const AuthContext = createContext({} as AuthContextType);

export default AuthContext

export function AuthContextProvider({ children }: AuthContextProps) {

    const [isAuthenticated, setIsAuthenticated] = useState(false)

    function signIn(jwtToken: string) {
        localStorage.setItem('@TUTOR-PE-AUTH', jwtToken)
        setIsAuthenticated(true)
    }

    function signOut() {
        localStorage.removeItem('@TUTOR-PE-AUTH')
        setIsAuthenticated(false)
    }

    useEffect(() => {
        const token = localStorage.getItem('@TUTOR-PE-AUTH');
        if (token) {
            setIsAuthenticated(true);
        }
    }, []);

    return (
        <AuthContext.Provider
            value={{
                signIn,
                signOut,
                isAuthenticated
            }}
        >
            {children}
        </AuthContext.Provider>
    )
}
