"use client";

import React, { useEffect, useState } from "react";
import { useAppStore } from "@/store/useAppStore";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export default function ProfilePage() {
  const { user, authUser, token, conversationSaveCount } = useAppStore();
  const [conversationCount, setConversationCount] = useState<number | null>(null);
  const initials = (user?.name || "").slice(0, 2).toUpperCase();

  const [showPwForm, setShowPwForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [pwMsg, setPwMsg] = useState("");

  useEffect(() => {
    if (!token) return;
    fetch(`${API_BASE_URL}/chat/conversations`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.data) setConversationCount(data.data.length);
      })
      .catch(() => {});
  }, [token, conversationSaveCount]);

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword) { setPwMsg("Fill in both fields"); return; }
    if (newPassword.length < 8) { setPwMsg("New password must be at least 8 characters"); return; }
    setPwMsg("");
    try {
      const res = await fetch(`${API_BASE_URL}/auth/change-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to change password");
      }
      setPwMsg("Password changed successfully");
      setCurrentPassword("");
      setNewPassword("");
      setShowPwForm(false);
    } catch (err) {
      setPwMsg(err instanceof Error ? err.message : "Failed to change password");
    }
  };

  return (
    <div className="min-h-full w-full bg-background text-on-surface pb-24 px-6 py-8">
      <div className="w-full max-w-4xl mx-auto space-y-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-primary-container/20 flex items-center justify-center flex-shrink-0">
            <span className="material-symbols-outlined text-primary text-[22px]" style={{ fontVariationSettings: "'FILL' 1" }}>account_circle</span>
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-[22px] font-bold text-on-surface leading-tight">Profile</h2>
            <p className="text-[12px] text-on-surface-variant font-mono">Manage your account details</p>
          </div>
        </div>

        {!user ? (
          <div className="glass-card p-10 rounded-2xl border border-outline-variant/20 text-center">
            <span className="material-symbols-outlined text-on-surface-variant text-5xl mb-3 block">person_off</span>
            <p className="text-body-md text-on-surface-variant">Please log in to view your profile.</p>
          </div>
        ) : (<>
          <div className="glass-card w-full p-6 rounded-2xl border border-outline-variant/20">
            <div className="flex items-center gap-5 mb-6 w-full">
              <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-secondary-container to-primary-container flex items-center justify-center shadow-lg flex-shrink-0">
                <span className="text-2xl font-black text-on-primary-container">{initials || "?"}</span>
              </div>
              <div className="flex-1 min-w-0 pr-4">
                <h3 className="text-[20px] font-bold text-on-surface truncate">{user.name}</h3>
                <p className="text-[13px] text-on-surface-variant mt-0.5 truncate">{authUser?.email || user.email}</p>
                <span className="inline-flex mt-2 px-3 py-0.5 rounded-full bg-primary-container/20 text-primary text-[11px] font-mono font-bold border border-primary/20">
                  {user.role || "USER"}
                </span>
              </div>
            </div>

            <div className="space-y-3 w-full">
              <div className="flex items-center justify-between gap-4 p-4 rounded-xl bg-surface-container-low border border-outline-variant/10 w-full">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <span className="material-symbols-outlined text-on-surface-variant text-[18px] flex-shrink-0">calendar_today</span>
                  <span className="text-[14px] text-on-surface truncate">Member since</span>
                </div>
                <span className="text-[13px] text-on-surface-variant font-mono flex-shrink-0">{user.created_at ? new Date(user.created_at).toLocaleDateString("en-US", { year: "numeric", month: "long" }) : "—"}</span>
              </div>
              <div className="flex items-center justify-between gap-4 p-4 rounded-xl bg-surface-container-low border border-outline-variant/10 w-full">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <span className="material-symbols-outlined text-on-surface-variant text-[18px] flex-shrink-0">workspace_premium</span>
                  <span className="text-[14px] text-on-surface truncate">Plan</span>
                </div>
                <span className="text-[13px] text-primary font-bold flex-shrink-0">Free</span>
              </div>
              <div className="flex items-center justify-between gap-4 p-4 rounded-xl bg-surface-container-low border border-outline-variant/10 w-full">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <span className="material-symbols-outlined text-on-surface-variant text-[18px] flex-shrink-0">forum</span>
                  <span className="text-[14px] text-on-surface truncate">Conversations</span>
                </div>
                <span className="text-[13px] text-on-surface-variant font-mono flex-shrink-0">{conversationCount !== null ? conversationCount : "—"}</span>
              </div>
            </div>
          </div>

          <div className="glass-card w-full p-6 rounded-2xl border border-outline-variant/20 space-y-3">
            <h3 className="text-[15px] font-bold text-on-surface mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[18px]">shield</span>
              Security
            </h3>
            <button
              onClick={() => { setShowPwForm(!showPwForm); setPwMsg(""); }}
              className="w-full flex items-center justify-between gap-4 px-4 py-3 rounded-xl bg-surface-container-high hover:bg-surface-container border border-outline-variant/10 hover:border-outline-variant/30 transition-colors group"
            >
              <span className="text-[14px] text-on-surface flex-1 text-left truncate">Change password</span>
              <span className={`material-symbols-outlined text-on-surface-variant group-hover:text-primary transition-colors text-[18px] flex-shrink-0 ${showPwForm ? "rotate-180" : ""}`}>expand_more</span>
            </button>
            {showPwForm && (
              <div className="px-4 pb-4 space-y-3">
                <input
                  type="password" value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Current password"
                  className="w-full bg-surface-container-high border border-outline-variant/30 rounded-xl px-4 py-2.5 text-[14px] text-on-surface focus:outline-none focus:border-primary/50 transition-colors"
                />
                <input
                  type="password" value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="New password (min 8 chars)"
                  className="w-full bg-surface-container-high border border-outline-variant/30 rounded-xl px-4 py-2.5 text-[14px] text-on-surface focus:outline-none focus:border-primary/50 transition-colors"
                />
                <button
                  onClick={handleChangePassword}
                  className="w-full py-2.5 bg-primary-container text-on-primary-container font-bold text-[13px] rounded-xl hover:brightness-110 active:scale-[0.98] transition-all"
                >
                  Update Password
                </button>
                {pwMsg && (
                  <p className={`text-[12px] ${pwMsg.includes("successfully") ? "text-tertiary" : "text-error"}`}>{pwMsg}</p>
                )}
              </div>
            )}
          </div>
        </>)}
      </div>
    </div>
  );
}