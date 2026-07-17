"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAppStore } from "@/store/useAppStore";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export default function SettingsPage() {
  const { authUser, token, logout } = useAppStore();
  const [theme, setThemeState] = useState<'dark' | 'light'>('dark');
  const [newEmail, setNewEmail] = useState('');
  const [showEmailInput, setShowEmailInput] = useState(false);
  const [emailMsg, setEmailMsg] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleteMsg, setDeleteMsg] = useState('');

  useEffect(() => {
    const saved = localStorage.getItem('vyron_theme');
    const t = saved === 'light' ? 'light' : 'dark';
    setThemeState(t);
    document.documentElement.setAttribute('data-theme', t);
  }, []);

  const toggleTheme = useCallback(() => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setThemeState(next);
    localStorage.setItem('vyron_theme', next);
    document.documentElement.setAttribute('data-theme', next);
  }, [theme]);

  const handleUpdateEmail = useCallback(async () => {
    if (!newEmail.trim() || !newEmail.includes('@')) {
      setEmailMsg('Please enter a valid email');
      return;
    }
    setEmailMsg('');
    try {
      const res = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ email: newEmail.trim() }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.error?.message || 'Failed to update email');
      }
      setEmailMsg('Email updated successfully');
      setShowEmailInput(false);
    } catch (err) {
      setEmailMsg(err instanceof Error ? err.message : 'Failed to update email');
    }
  }, [newEmail, token]);

  const handleDeleteAccount = useCallback(async () => {
    setDeleteMsg('');
    try {
      const res = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'DELETE',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.error?.message || 'Failed to delete account');
      }
      logout();
    } catch (err) {
      setDeleteMsg(err instanceof Error ? err.message : 'Failed to delete account');
    }
  }, [token, logout]);

  return (
    <div className="min-h-full w-full bg-background text-on-surface pb-24 px-6 py-8">
      <div className="w-full max-w-4xl mx-auto space-y-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-primary-container/20 flex items-center justify-center flex-shrink-0">
            <span className="material-symbols-outlined text-primary text-[22px]" style={{ fontVariationSettings: "'FILL' 1" }}>settings</span>
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-[22px] font-bold text-on-surface leading-tight">Settings</h2>
            <p className="text-[12px] text-on-surface-variant font-mono">System configuration & preferences</p>
          </div>
        </div>

        {/* Preferences */}
        <div className="glass-card w-full p-6 rounded-2xl border border-outline-variant/20 space-y-5">
          <h3 className="text-[16px] font-bold text-on-surface flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[18px]">tune</span>
            Preferences
          </h3>
          <div className="flex items-center justify-between gap-4 py-3 w-full">
            <div className="flex-1 min-w-0 pr-4">
              <p className="text-[14px] font-medium text-on-surface">Theme</p>
              <p className="text-[12px] text-on-surface-variant mt-0.5">Switch between dark and light mode</p>
            </div>
            <button
              onClick={toggleTheme}
              className="whitespace-nowrap px-4 py-2 rounded-xl text-[13px] font-bold transition-all flex-shrink-0 bg-primary-container text-on-primary-container hover:brightness-110 active:scale-95 shadow-md shadow-primary-container/20 flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-[16px]">{theme === 'dark' ? 'dark_mode' : 'light_mode'}</span>
              {theme === 'dark' ? 'Dark' : 'Light'}
            </button>
          </div>
        </div>

        {/* Account */}
        <div className="glass-card w-full p-6 rounded-2xl border border-outline-variant/20 space-y-5">
          <h3 className="text-[16px] font-bold text-on-surface flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[18px]">manage_accounts</span>
            Account
          </h3>

          <div className="flex items-center justify-between gap-4 py-3 border-b border-outline-variant/10 w-full">
            <div className="flex-1 min-w-0 pr-4">
              <p className="text-[14px] font-medium text-on-surface">Email</p>
              <p className="text-[12px] text-on-surface-variant mt-0.5">{authUser?.email || 'Not logged in'}</p>
            </div>
            <button
              onClick={() => { setShowEmailInput(!showEmailInput); setEmailMsg(''); }}
              className="whitespace-nowrap px-4 py-2 bg-primary-container text-on-primary-container text-[13px] font-bold rounded-xl hover:brightness-110 active:scale-95 transition-all shadow-md shadow-primary-container/20 flex-shrink-0"
            >
              Update
            </button>
          </div>
          {showEmailInput && (
            <div className="flex items-center gap-3 w-full">
              <input
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                placeholder="New email address"
                className="flex-1 min-w-0 bg-surface-container-high border border-outline-variant/30 rounded-xl px-4 py-2 text-[14px] text-on-surface focus:outline-none focus:border-primary/50 transition-colors"
              />
              <button
                onClick={handleUpdateEmail}
                className="whitespace-nowrap px-4 py-2 bg-primary text-on-primary text-[13px] font-bold rounded-xl hover:brightness-110 active:scale-95 transition-all flex-shrink-0"
              >
                Save
              </button>
            </div>
          )}
          {emailMsg && (
            <p className={`text-[12px] ${emailMsg.includes('successfully') ? 'text-tertiary' : 'text-error'}`}>{emailMsg}</p>
          )}

          <div className="flex items-center justify-between gap-4 py-3 border-t border-outline-variant/10 w-full">
            <div className="flex-1 min-w-0 pr-4">
              <p className="text-[14px] font-medium text-on-surface">Logout</p>
              <p className="text-[12px] text-on-surface-variant mt-0.5">Sign out of your account</p>
            </div>
            <button
              onClick={() => logout()}
              className="whitespace-nowrap px-4 py-2 bg-surface-container-high text-on-surface-variant text-[13px] font-bold rounded-xl hover:bg-error/10 hover:text-error active:scale-95 transition-all border border-outline-variant/20 flex-shrink-0"
            >
              Logout
            </button>
          </div>

          <div className="flex items-center justify-between gap-4 py-3 w-full">
            <div className="flex-1 min-w-0 pr-4">
              <p className="text-[14px] font-medium text-on-surface">Delete account</p>
              <p className="text-[12px] text-on-surface-variant mt-0.5">Permanently remove all data</p>
            </div>
            {!deleteConfirm ? (
              <button
                onClick={() => setDeleteConfirm(true)}
                className="whitespace-nowrap px-4 py-2 bg-error/10 text-error text-[13px] font-bold rounded-xl hover:bg-error/20 active:scale-95 transition-all border border-error/20 flex-shrink-0"
              >
                Delete
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setDeleteConfirm(false)}
                  className="whitespace-nowrap px-3 py-2 text-[12px] font-bold rounded-xl bg-surface-container-high text-on-surface-variant hover:brightness-110 transition-all flex-shrink-0"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteAccount}
                  className="whitespace-nowrap px-3 py-2 bg-error text-on-error text-[12px] font-bold rounded-xl hover:brightness-110 active:scale-95 transition-all flex-shrink-0"
                >
                  Confirm
                </button>
              </div>
            )}
          </div>
          {deleteMsg && (
            <p className="text-[12px] text-error">{deleteMsg}</p>
          )}
        </div>
      </div>
    </div>
  );
}
