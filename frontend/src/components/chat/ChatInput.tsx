"use client";

import { useState, useRef, useEffect, FormEvent } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Re-focus after reply arrives (improves one-handed mobile flow)
  useEffect(() => {
    if (!disabled) inputRef.current?.focus();
  }, [disabled]);

  const trimmed = value.trim();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  return (
    <div className="shrink-0 border-t border-slate-800/40 bg-[var(--surface)] px-4 py-3">
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-2"
      >
        <div className="relative flex-1">
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Apna message likhein…"
            disabled={disabled}
            className="w-full rounded-2xl border border-slate-700/50 bg-[var(--surface)] px-4 py-3 pr-12 text-[0.9375rem] text-slate-100 placeholder:text-slate-500 outline-none transition-colors focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/25 disabled:opacity-50"
          />
        </div>

        <button
          type="submit"
          disabled={!trimmed || disabled}
          aria-label="Bhejein"
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-white transition-all hover:bg-emerald-500 active:scale-95 disabled:opacity-30 disabled:hover:bg-emerald-600 disabled:active:scale-100"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 19V5" />
            <path d="M5 12l7-7 7 7" />
          </svg>
        </button>
      </form>
    </div>
  );
}
