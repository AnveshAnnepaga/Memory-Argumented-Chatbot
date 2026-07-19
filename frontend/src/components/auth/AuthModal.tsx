'use client';

import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';

export function AuthModal() {
  const { authModalOpen, setAuthModalOpen, login, register, isAuthenticated } = useAppStore();

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!authModalOpen || isAuthenticated) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register(email, password, fullName || undefined);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setError('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setAuthModalOpen(false)} />
      <div className="relative w-full max-w-md glass-surface rounded-2xl border border-outline-variant/20 shadow-2xl overflow-hidden animate-in zoom-in-95">
        <div className="px-6 pt-6 pb-4 border-b border-outline-variant/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 flex items-center justify-center overflow-hidden">
                <img src="/vyron-logo.png" alt="Vyron" className="w-full h-full object-contain rounded-lg" />
              </div>
              <span className="text-[18px] font-black text-primary tracking-tight">Vyron AI</span>
            </div>
            <button
              onClick={() => setAuthModalOpen(false)}
              className="p-2 rounded-xl hover:bg-surface-container text-on-surface-variant hover:text-on-surface transition-colors"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
        </div>

        <div className="px-6 py-6">
          <h3 className="text-[22px] font-bold text-on-surface mb-1">
            {mode === 'login' ? 'Welcome Back' : 'Create Account'}
          </h3>
          <p className="text-[13px] text-on-surface-variant mb-6">
            {mode === 'login'
              ? 'Sign in to your Vyron AI account'
              : 'Register for a new Vyron AI account'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="text-[12px] font-mono text-on-surface-variant uppercase tracking-wider mb-1.5 block">
                  Full Name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-surface-container-high border border-outline-variant/30 rounded-xl px-4 py-2.5 text-[14px] text-on-surface focus:outline-none focus:border-primary/50 transition-colors"
                  placeholder="Your name"
                  maxLength={100}
                />
              </div>
            )}

            <div>
              <label className="text-[12px] font-mono text-on-surface-variant uppercase tracking-wider mb-1.5 block">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-surface-container-high border border-outline-variant/30 rounded-xl px-4 py-2.5 text-[14px] text-on-surface focus:outline-none focus:border-primary/50 transition-colors"
                placeholder="you@example.com"
                required
              />
            </div>

            <div>
              <label className="text-[12px] font-mono text-on-surface-variant uppercase tracking-wider mb-1.5 block">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-surface-container-high border border-outline-variant/30 rounded-xl px-4 py-2.5 text-[14px] text-on-surface focus:outline-none focus:border-primary/50 transition-colors"
                placeholder={mode === 'register' ? 'At least 8 characters' : 'Your password'}
                required
                minLength={8}
                maxLength={128}
              />
            </div>

            {error && (
              <div className="px-4 py-3 rounded-xl bg-error/10 border border-error/20 text-error text-[13px] font-medium">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-primary-container text-on-primary-container font-bold text-[14px] rounded-xl hover:brightness-110 active:scale-[0.98] transition-all shadow-lg shadow-primary-container/20 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 rounded-full border-2 border-on-primary-container border-t-transparent animate-spin" />
                  {mode === 'login' ? 'Signing in...' : 'Creating account...'}
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[18px]">
                    {mode === 'login' ? 'login' : 'person_add'}
                  </span>
                  {mode === 'login' ? 'Sign In' : 'Create Account'}
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={switchMode}
              className="text-[13px] text-primary hover:text-primary/80 transition-colors font-medium"
            >
              {mode === 'login'
                ? "Don't have an account? Sign up"
                : 'Already have an account? Sign in'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
