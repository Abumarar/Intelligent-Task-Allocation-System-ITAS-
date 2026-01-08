import React, { useMemo, useState, useCallback } from "react";
import { api } from "../api/client";
import { AuthContext, type AuthCtx, type Role, type User } from "./context";

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const demoEnabled = import.meta.env.DEV || import.meta.env.VITE_ENABLE_DEMO === "true";

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

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
