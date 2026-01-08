import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "./hooks";

export function ProtectedRoute({
    children,
    allow,
}: {
    children: React.ReactNode;
    allow?: ("PM" | "EMPLOYEE")[];
}) {
    const { user } = useAuth();
    if (!user) return <Navigate to="/login" replace />;
    if (allow && !allow.includes(user.role)) return <Navigate to="/" replace />;
    return <>{children}</>;
}