"use client";

/**
 * VOICE-3 — plays an assistant reply aloud.
 *
 * Owns a single <audio> element via a ref. `speak(id, text)` fetches + plays;
 * the caller tracks per-message state via `status` + `activeId`. Autoplay
 * rejection surfaces as "blocked" (the UI offers a tap-to-play button) rather
 * than an error — the reply text is always on screen regardless.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { synthesizeSpeech } from "./tts";

export type SpeechStatus =
  | "idle"
  | "loading"
  | "playing"
  | "blocked"
  | "error";

export interface UseReplySpeech {
  status: SpeechStatus;
  /** id of the message currently loading/playing, or null. */
  activeId: string | null;
  speak: (id: string, text: string) => Promise<void>;
  stop: () => void;
}

export function useReplySpeech(): UseReplySpeech {
  const [status, setStatus] = useState<SpeechStatus>("idle");
  const [activeId, setActiveId] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const urlRef = useRef<string | null>(null);
  // Guards against a slow fetch resolving after the user started another clip.
  const requestSeq = useRef(0);

  const cleanupUrl = useCallback(() => {
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
  }, []);

  const stop = useCallback(() => {
    requestSeq.current += 1;
    audioRef.current?.pause();
    audioRef.current = null;
    cleanupUrl();
    setStatus("idle");
    setActiveId(null);
  }, [cleanupUrl]);

  const speak = useCallback(
    async (id: string, text: string) => {
      if (!text.trim()) return;
      const seq = ++requestSeq.current;

      // Tear down any current playback.
      audioRef.current?.pause();
      audioRef.current = null;
      cleanupUrl();

      setActiveId(id);
      setStatus("loading");

      let blob: Blob;
      try {
        blob = await synthesizeSpeech(text);
      } catch {
        if (seq === requestSeq.current) setStatus("error");
        return;
      }
      if (seq !== requestSeq.current) return; // superseded

      const url = URL.createObjectURL(blob);
      urlRef.current = url;

      // Build the element fully as a local, then hand it to the ref once.
      const el = new Audio();
      el.src = url;
      el.onended = () => {
        if (seq === requestSeq.current) {
          setStatus("idle");
          setActiveId(null);
          cleanupUrl();
        }
      };
      el.onerror = () => {
        if (seq === requestSeq.current) setStatus("error");
      };
      audioRef.current = el;

      try {
        await el.play();
        if (seq === requestSeq.current) setStatus("playing");
      } catch {
        // Autoplay policy — the caller shows a tap-to-play affordance.
        if (seq === requestSeq.current) setStatus("blocked");
      }
    },
    [cleanupUrl],
  );

  useEffect(() => {
    const urlAtMount = urlRef;
    const audioAtMount = audioRef;
    return () => {
      audioAtMount.current?.pause();
      if (urlAtMount.current) URL.revokeObjectURL(urlAtMount.current);
    };
  }, []);

  return { status, activeId, speak, stop };
}
