import React, { useMemo, useState, useCallback } from "react";
import { api } from "../api/client";
import { AuthContext, type AuthCtx, type Role, type User } from "./context";

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const demoEnabled = import.meta.env.DEV || import.meta.env.VITE_ENABLE_DEMO === "true";

    React.useEffect(() => {
        const restoreSession = async () => {
            const token = localStorage.getItem("itas_token");
            if (!token) {
                setLoading(false);
                return;
            }

            // Handle demo session
            if (token === "demo") {
                // Try to guess role or default to PM
                const demoUser: User = { id: "demo-user", name: "Demo PM", role: "PM" };
                setUser(demoUser);
                setLoading(false);
                return;
            }

            try {
                const res = await api.get("/auth/login");
                if (res.data.user) {
                    setUser(res.data.user);
                } else {
                    localStorage.removeItem("itas_token");
                }
            } catch (error) {
                console.error("Session restore failed", error);
                localStorage.removeItem("itas_token");
            } finally {
                setLoading(false);
            }
        };

        restoreSession();
    }, []);

    const login = useCallback(async (email: string, password: string) => {
        try {
            const res = await api.post("/auth/login", { email, password });
            if (res.data.token && res.data.user) {
                localStorage.setItem("itas_token", res.data.token);
                setUser(res.data.user);
            } else {
                throw new Error("Invalid response from server");
            }
        } catch (error: unknown) {
            console.error("Login error:", error);
            throw error;
        }
    }, []);

    const logout = () => {
        localStorage.removeItem("itas_token");
        setUser(null);
    };

    // Memoize demoLogin to avoid dependency warning
    const demoLogin = useMemo(() => {
        if (!demoEnabled) return undefined;
        return (role: Role = "PM") => {
            const demoUser: User = {
                id: "demo-user",
                name: role === "PM" ? "Demo PM" : "Demo Employee",
                role,
            };
            localStorage.setItem("itas_token", "demo");
            setUser(demoUser);
        };
    }, [demoEnabled]);

    const value: AuthCtx = useMemo(() => ({ user, login, logout, demoLogin }), [user, login, demoLogin]);

    if (loading) {
        return <div className="min-h-screen flex items-center justify-center bg-slate-50 text-indigo-600">Loading...</div>;
    }

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
