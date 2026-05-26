import React, { Suspense, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "./auth/AuthProvider";
import { useAuth } from "./auth/hooks";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { ThemeProvider } from "./context/ThemeContext";
import AppShell, { type NavItem } from "./components/layout/AppShell";
import LoadingScreen from "./components/LoadingScreen";

// Lazy-loaded components
const Login = React.lazy(() => import("./pages/Login"));
const PMDashboard = React.lazy(() => import("./pages/pm/Dashboard"));
const PMReports = React.lazy(() => import("./pages/pm/Reports"));
const TaskCreate = React.lazy(() => import("./pages/pm/TaskCreate"));
const Employees = React.lazy(() => import("./pages/pm/Employees"));
const Projects = React.lazy(() => import("./pages/pm/Projects"));
const Tasks = React.lazy(() => import("./pages/pm/Tasks"));
const MyProfile = React.lazy(() => import("./pages/employee/MyProfile"));
const Settings = React.lazy(() => import("./pages/Settings"));
const NotFound = React.lazy(() => import("./pages/NotFound"));

const queryClient = new QueryClient();
const pmNav: NavItem[] = [
  { label: "Dashboard", to: "/pm/dashboard", meta: "Pulse" },
  { label: "Reports", to: "/pm/reports", meta: "Insights" },
  { label: "Projects", to: "/pm/projects", meta: "Manage" },
  { label: "Employees", to: "/pm/employees", meta: "Skills" },
  { label: "Settings", to: "/pm/settings", meta: "Config" },
];
const employeeNav: NavItem[] = [
  { label: "My Profile", to: "/employee/profile", meta: "Overview" },
  { label: "Settings", to: "/employee/settings", meta: "Config" },
];

function HomeRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return user.role === "PM" ? (
    <Navigate to="/pm/dashboard" replace />
  ) : (
    <Navigate to="/employee/profile" replace />
  );
}

export default function App() {
  const [isLoading, setIsLoading] = useState(true);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <Toaster position="top-right" />
        {isLoading && <LoadingScreen onComplete={() => setIsLoading(false)} />}
        <AuthProvider>
          <BrowserRouter>
            <Suspense fallback={<LoadingScreen onComplete={() => {}} />}>
              <Routes>
                <Route path="/" element={<HomeRedirect />} />
                <Route path="/login" element={<Login />} />

                <Route
                  element={
                    <ProtectedRoute allow={["PM"]}>
                      <AppShell nav={pmNav} />
                    </ProtectedRoute>
                  }
                >
                  <Route path="/pm/dashboard" element={<PMDashboard />} />
                  <Route path="/pm/reports" element={<PMReports />} />
                  <Route path="/pm/projects" element={<Projects />} />
                  <Route path="/pm/projects/:projectId" element={<Tasks />} />
                  <Route path="/pm/tasks" element={<Tasks />} /> {/* Keep for backward compat or global view if needed */}
                  <Route path="/pm/employees" element={<Employees />} />
                  <Route path="/pm/tasks/new" element={<TaskCreate />} />
                  <Route path="/pm/settings" element={<Settings />} />
                </Route>

                <Route
                  element={
                    <ProtectedRoute allow={["EMPLOYEE"]}>
                      <AppShell nav={employeeNav} />
                    </ProtectedRoute>
                  }
                >
                  <Route path="/employee/profile" element={<MyProfile />} />
                  <Route path="/employee/settings" element={<Settings />} />
                </Route>

                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
