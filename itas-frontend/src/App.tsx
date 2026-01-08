import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./auth/AuthProvider";
import { useAuth } from "./auth/hooks";
import { ProtectedRoute } from "./auth/ProtectedRoute";

import Login from "./pages/Login.tsx";
import PMDashboard from "./pages/pm/Dashboard.tsx";
import TaskCreate from "./pages/pm/TaskCreate.tsx";
import Employees from "./pages/pm/Employees.tsx";
import Tasks from "./pages/pm/Tasks.tsx";
import MyProfile from "./pages/employee/MyProfile.tsx";
import AppShell, { type NavItem } from "./components/layout/AppShell";

const queryClient = new QueryClient();
const pmNav: NavItem[] = [
  { label: "Dashboard", to: "/pm/dashboard", meta: "Pulse" },
  { label: "Tasks", to: "/pm/tasks", meta: "Manage" },
  { label: "Employees", to: "/pm/employees", meta: "Skills" },
];
const employeeNav: NavItem[] = [
  { label: "My Profile", to: "/employee/profile", meta: "Overview" },
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
  return (
    <QueryClientProvider client={queryClient}>
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
              <Route path="/pm/tasks" element={<Tasks />} />
              <Route path="/pm/employees" element={<Employees />} />
              <Route path="/pm/tasks/new" element={<TaskCreate />} />
            </Route>

            <Route
              element={
                <ProtectedRoute allow={["EMPLOYEE"]}>
                  <AppShell nav={employeeNav} />
                </ProtectedRoute>
              }
            >
              <Route path="/employee/profile" element={<MyProfile />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
