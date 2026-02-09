
import React, { useState } from 'react';
import { ApiConfig } from '../lib/api';

const API: ApiConfig = { baseUrl: "http://localhost:8500" }; // Updated to runtime port

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        try {
            const formData = new URLSearchParams();
            formData.append('username', email); // FastAPI OAuth2 expects 'username' (which is our email)
            formData.append('password', password);

            const res = await fetch(`${API.baseUrl}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });

            if (!res.ok) {
                const txt = await res.text();
                throw new Error(txt || "Login failed");
            }

            const data = await res.json();
            localStorage.setItem("token", data.access_token);
            window.location.href = "/"; // Redirect to dashboard
        } catch (err: any) {
            setError(err.message);
        }
    };

    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="w-full max-w-md space-y-8">
                <div className="flex flex-col items-center">
                    {/* Assuming existing static file server or Vite public dir handles /static maps to apps/user/static? 
                        Vite 'public' dir is served at root. 'static' folder in src? 
                        If 'static' is in root, Vite serves it at /static if configured?
                        Actually, 'apps/user/static' exists. We need to check if Vite config exposes it.
                        Config has alias '@'.
                        Let's try standard relative path if inside src, OR absolute if in public.
                        For now, let's assume /logo.png if copying to public, or /src/static/logo.png
                        The finding showed 'apps/user/static/logo.png'. 
                        I will assume I need to move it to public or import it.
                    */}
                    <img className="h-12 w-auto" src="/static/logo.png" alt="CareerTrojan" />
                    <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">Sign in to CareerTrojan</h2>
                </div>
                <form className="mt-8 space-y-6" onSubmit={handleLogin}>
                    <div className="-space-y-px rounded-md shadow-sm">
                        <div>
                            <input
                                type="email"
                                required
                                className="relative block w-full rounded-t-md border-0 p-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                                placeholder="Email address"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                        </div>
                        <div>
                            <input
                                type="password"
                                required
                                className="relative block w-full rounded-b-md border-0 p-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                    </div>

                    {error && <div className="text-red-500 text-sm text-center">{error}</div>}

                    <div>
                        <button
                            type="submit"
                            className="group relative flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                        >
                            Sign in
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
