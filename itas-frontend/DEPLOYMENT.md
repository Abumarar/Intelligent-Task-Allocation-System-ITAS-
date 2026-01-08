Vercel deployment checklist

This file contains steps and environment variable tips to deploy the frontend to Vercel (https://vercel.com).

Required environment variables (set in Vercel project settings):
- VITE_API_BASE_URL: URL of the backend API (example: https://api.jobtecacademy.com/api or https://jobtecacademy.com/api)

Quick deploy steps:
1. Connect your repo to Vercel and create a new project.
2. Build Command: npm run build (or yarn build)
3. Output Directory: dist (Vite default)
4. Set `VITE_API_BASE_URL` to your backend URL (for example: https://api.jobtecacademy.com/api). If you instead host the frontend and backend under the same domain, you can omit this and the client will use the same origin at runtime.
5. Add your custom domain (www.jobtecacademy.com and jobtecacademy.com) in Vercel dashboard and configure DNS.

Notes
- For previews/staging, set VITE_API_BASE_URL to the Render URL of your backend.
- The frontend will make authenticated requests with Authorization: Bearer <token> header in localStorage; make sure CORS on the backend allows credentials and the frontend origin.
