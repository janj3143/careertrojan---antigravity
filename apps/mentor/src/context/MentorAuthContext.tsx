import React, { createContext, useContext, useState, useEffect } from 'react';

interface MentorUser {
    id: string;
    email: string;
    full_name?: string;
    role: 'mentor';
    verified: boolean;
}

interface MentorAuthContextType {
    user: MentorUser | null;
    token: string | null;
    isAuthenticated: boolean;
    loading: boolean;
    login: (token: string, user: MentorUser) => void;
    logout: () => void;
}

const MentorAuthContext = createContext<MentorAuthContextType | undefined>(undefined);

export function MentorAuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<MentorUser | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem("mentor_token"));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const storedToken = localStorage.getItem("mentor_token");
        const storedUser = localStorage.getItem("mentor_user");

        if (storedToken) {
            setToken(storedToken);
            if (storedUser) {
                try {
                    setUser(JSON.parse(storedUser));
                } catch (e) {
                    console.error("Failed to parse mentor user from storage");
                }
            }
        }
        setLoading(false);
    }, []);

    const login = (newToken: string, newUser: MentorUser) => {
        localStorage.setItem("mentor_token", newToken);
        localStorage.setItem("mentor_user", JSON.stringify(newUser));
        setToken(newToken);
        setUser(newUser);
    };

    const logout = () => {
        localStorage.removeItem("mentor_token");
        localStorage.removeItem("mentor_user");
        setToken(null);
        setUser(null);
        window.location.href = "/mentor/login";
    };

    const value = {
        user,
        token,
        isAuthenticated: !!token,
        loading,
        login,
        logout
    };

    return (
        <MentorAuthContext.Provider value={value}>
            {children}
        </MentorAuthContext.Provider>
    );
}

export function useMentorAuth() {
    const context = useContext(MentorAuthContext);
    if (context === undefined) {
        throw new Error("useMentorAuth must be used within a MentorAuthProvider");
    }
    return context;
}
