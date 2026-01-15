import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./auth/AuthProvider";
import { useAuth } from "./auth/hooks";
import { ProtectedRoute } from "./auth/ProtectedRoute";

import Login from "./pages/Login.tsx";
import PMDashboard from "./pages/pm/Dashboard.tsx";
import TaskCreate from "./pages/pm/TaskCreate.tsx";
import Employees from "./pages/pm/Employees.tsx";
import Projects from "./pages/pm/Projects.tsx";
import Tasks from "./pages/pm/Tasks.tsx";
import MyProfile from "./pages/employee/MyProfile.tsx";
import Settings from "./pages/Settings.tsx";
import NotFound from "./pages/NotFound.tsx";
import { ThemeProvider } from "./context/ThemeContext.tsx";
import AppShell, { type NavItem } from "./components/layout/AppShell";

const queryClient = new QueryClient();
const pmNav: NavItem[] = [
  { label: "Dashboard", to: "/pm/dashboard", meta: "Pulse" },
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

import { useState } from "react";
import LoadingScreen from "./components/LoadingScreen";

export default function App() {
  const [isLoading, setIsLoading] = useState(true);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        {isLoading && <LoadingScreen onComplete={() => setIsLoading(false)} />}
        <AuthProvider>
          <BrowserRouter>
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
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
