import React, { createContext, useContext, useState, useEffect } from 'react';

interface AdminUser {
    id: string;
    email: string;
    full_name?: string;
    role: 'admin' | 'super_admin';
}

interface AdminAuthContextType {
    user: AdminUser | null;
    token: string | null;
    isAuthenticated: boolean;
    loading: boolean;
    login: (token: string, user: AdminUser) => void;
    logout: () => void;
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(undefined);

export function AdminAuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<AdminUser | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem("admin_token"));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const storedToken = localStorage.getItem("admin_token");
        const storedUser = localStorage.getItem("admin_user");

        if (storedToken) {
            setToken(storedToken);
            if (storedUser) {
                try {
                    setUser(JSON.parse(storedUser));
                } catch (e) {
                    console.error("Failed to parse admin user from storage");
                }
            }
        }
        setLoading(false);
    }, []);

    const login = (newToken: string, newUser: AdminUser) => {
        localStorage.setItem("admin_token", newToken);
        localStorage.setItem("admin_user", JSON.stringify(newUser));
        setToken(newToken);
        setUser(newUser);
    };

    const logout = () => {
        localStorage.removeItem("admin_token");
        localStorage.removeItem("admin_user");
        setToken(null);
        setUser(null);
        window.location.href = "/admin/login";
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
        <AdminAuthContext.Provider value={value}>
            {children}
        </AdminAuthContext.Provider>
    );
}

export function useAdminAuth() {
    const context = useContext(AdminAuthContext);
    if (context === undefined) {
        throw new Error("useAdminAuth must be used within an AdminAuthProvider");
    }
    return context;
}
