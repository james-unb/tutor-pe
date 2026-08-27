import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { Login } from './pages/Login';
import { Simulados } from './pages/Simulados';
import { SimuladoPlayer } from './pages/SimuladoPlayer';
import { SimuladoPerformance } from './pages/SimuladoPerformance';
import { Chat } from './pages/Chat';
import './styles/global.scss';

import { GoogleOAuthProvider } from '@react-oauth/google';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

import { AuthContextProvider } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import { useContext } from 'react';
import AuthContext from './contexts/AuthContext';

const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useContext(AuthContext);

  if (!isAuthenticated) {
    return <Login />;
  }

  return children;
};

function App() {
  return (
    <ThemeProvider>
      <AuthContextProvider>
        <BrowserRouter>
          <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<MainLayout />}>
                <Route index element={<Navigate to="/simulados" replace />} />
                <Route path="simulados" element={<PrivateRoute><Simulados /></PrivateRoute>} />
                <Route path="simulados/:id/play" element={<PrivateRoute><SimuladoPlayer /></PrivateRoute>} />
                <Route path="simulados/:id/performance" element={<PrivateRoute><SimuladoPerformance /></PrivateRoute>} />
                <Route path="chat/:id" element={<PrivateRoute><Chat /></PrivateRoute>} />
                <Route path="*" element={<Navigate to="/simulados" replace />} />
              </Route>
            </Routes>
          </GoogleOAuthProvider>
        </BrowserRouter>
      </AuthContextProvider >
    </ThemeProvider>
  );
}

export default App;
