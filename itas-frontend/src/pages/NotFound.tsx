
import { Link } from "react-router-dom";

export default function NotFound() {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50 text-center p-6">
            <div className="w-24 h-24 bg-slate-200 rounded-full flex items-center justify-center text-4xl mb-6">
                🤔
            </div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Page Not Found</h1>
            <p className="text-slate-600 mb-8 max-w-md">
                We couldn't find the page you're looking for. It might have been moved or doesn't exist.
            </p>
            <Link to="/" className="btn btn-primary">
                Go Home
            </Link>
        </div>
    );
}
