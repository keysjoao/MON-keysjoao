'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { apiClient } from '@/lib/api';

interface User {
    id: string;
    email: string;
    name: string;
}

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, name: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Check for existing session on mount
    useEffect(() => {
        const checkAuth = async () => {
            const token = apiClient.getToken();
            if (token) {
                try {
                    const userData = await apiClient.getMe();
                    setUser({
                        id: userData.id,
                        email: userData.email,
                        name: userData.name,
                    });
                } catch (error) {
                    // Token is invalid, clear it
                    apiClient.logout();
                }
            }
            setIsLoading(false);
        };

        checkAuth();
    }, []);

    const login = useCallback(async (email: string, password: string) => {
        const result = await apiClient.login(email, password);
        setUser(result.user);
    }, []);

    const register = useCallback(async (email: string, password: string, name: string) => {
        const result = await apiClient.register(email, password, name);
        setUser(result.user);
    }, []);

    const logout = useCallback(() => {
        apiClient.logout();
        setUser(null);
    }, []);

    return (
        <AuthContext.Provider
            value={{
                user,
                isLoading,
                isAuthenticated: !!user,
                login,
                register,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
