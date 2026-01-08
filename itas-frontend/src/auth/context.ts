import { createContext } from "react";

export type Role = "PM" | "EMPLOYEE";

export type User = {
    id: string;
    name: string;
    role: Role;
};

export type AuthCtx = {
    user: User | null;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    demoLogin?: (role?: Role) => void;
};

export const AuthContext = createContext<AuthCtx | null>(null);
