import React, { useState, useEffect } from "react";
import { useAuth } from "../auth/hooks";
import { useTheme } from "../context/ThemeContext";
import { api } from "../api/client";

export default function Settings() {
    const { user } = useAuth();
    const { theme, toggleTheme } = useTheme();

    const [name, setName] = useState(user?.name || "");
    const [email, setEmail] = useState(user?.email || "");
    const [password, setPassword] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

    // Sync state when user loads
    useEffect(() => {
        if (user) {
            setName(user.name);
            if (user.email) setEmail(user.email);
        }
    }, [user]);

    const handleUpdateProfile = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setMessage(null);

        const data: Record<string, string> = {};
        if (name && name !== user?.name) data.name = name;
        if (email && email !== user?.email) data.email = email;
        if (password) data.password = password;

        if (Object.keys(data).length === 0) {
            setIsSubmitting(false);
            return;
        }

        try {
            await api.patch("/auth/login", data);
            setMessage({ type: "success", text: "Profile updated successfully. Please refresh to see changes." });
            setPassword("");
        } catch (err: any) {
            setMessage({ type: "error", text: err.response?.data?.message || "Failed to update profile" });
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="page fade-in">
            <div className="page-hero">
                <div>
                    <div className="eyebrow">Configuration</div>
                    <h1 className="page-title">Settings</h1>
                    <p className="lead">Manage your preferences and account security.</p>
                </div>
            </div>

            <div className="form-layout">
                <div className="form-column">

                    {/* Appearance Section */}
                    <div className="card">
                        <div className="card-header">
                            <h2 className="card-title">Appearance</h2>
                        </div>
                        <div className="field">
                            <div className="flex items-center justify-between p-4 rounded-xl border border-[var(--line)] bg-[var(--bg)]">
                                <div>
                                    <div className="font-semibold text-lg">Dark Mode</div>
                                    <div className="text-[var(--muted)] text-sm">Switch between light and dark themes</div>
                                </div>
                                <button
                                    onClick={toggleTheme}
                                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:ring-offset-2 ${theme === "dark" ? "bg-[var(--accent)]" : "bg-gray-200"
                                        }`}
                                >
                                    <span
                                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${theme === "dark" ? "translate-x-6" : "translate-x-1"
                                            }`}
                                    />
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Profile Section */}
                    <form className="card" onSubmit={handleUpdateProfile}>
                        <div className="card-header">
                            <h2 className="card-title">Profile & Security</h2>
                        </div>

                        {message && (
                            <div className={`p-3 rounded-lg text-sm mb-4 ${message.type === "success"
                                    ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                                    : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                                }`}>
                                {message.text}
                            </div>
                        )}

                        <div className="form-section">
                            <div className="grid-2">
                                <div className="field">
                                    <label className="field-label">Full Name</label>
                                    <input
                                        type="text"
                                        className="input"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        placeholder="Your Name"
                                    />
                                </div>
                                <div className="field">
                                    <label className="field-label">Email Address</label>
                                    <input
                                        type="email"
                                        className="input"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        placeholder="name@company.com"
                                    />
                                </div>
                            </div>

                            <div className="field">
                                <label className="field-label">New Password</label>
                                <input
                                    type="password"
                                    className="input"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="Enter new password to change"
                                    minLength={6}
                                />
                                <p className="text-xs text-[var(--muted)]">Leave blank to keep current password.</p>
                            </div>
                        </div>

                        <div className="form-actions mt-6">
                            <button
                                type="submit"
                                className="btn btn-primary"
                                disabled={isSubmitting}
                            >
                                {isSubmitting ? "Saving..." : "Save Changes"}
                            </button>
                        </div>
                    </form>

                </div>
            </div>
        </div>
    );
}
