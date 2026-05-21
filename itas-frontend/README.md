# Intelligent Task Allocation System (ITAS) - Frontend

This is the frontend application for the Intelligent Task Allocation System (ITAS), a web-based platform designed to optimize software development task allocation using AI and data-driven assignment algorithms.

## Tech Stack
- **Framework:** React + TypeScript + Vite
- **Styling:** Tailwind CSS
- **State Management & Data Fetching:** TanStack Query (React Query)
- **Routing:** React Router v6

## Features
- **Project Manager Dashboard:** View real-time analytics on employee workload, task completion rates, and project progress.
- **Kanban Task Board:** Drag-and-drop or status-based task management.
- **AI Matching Integration:** Visualize the AI recommendations for task assignment with specific skill overlaps and performance predictions.
- **Performance Rating System:** Detailed modal interfaces for Project Managers to provide comprehensive feedback on completed tasks.
- **Employee Portal:** A personal view for employees to manage their tasks, workload, and skills profile.

## Setup Instructions

### 1. Prerequisites
- Node.js (v18 or higher)
- npm or yarn

### 2. Installation
```bash
cd itas-frontend
npm install
```

### 3. Environment Configuration
Create a `.env` file in the `itas-frontend` directory to point to your local or remote backend:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### 4. Running the Development Server
```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

## Building for Production
```bash
npm run build
```
The output will be generated in the `dist/` directory.

## Deployment
See `DEPLOYMENT.md` for instructions to deploy the frontend to Vercel or similar platforms. Ensure you set the `VITE_API_BASE_URL` environment variable in your deployment platform to point to your live backend.
