import { useCallback, useEffect, useRef, useState } from "react";

export const MUSIC = {
  title: "Adrift Among Infinite Stars",
  artist: "Scott Buckley",
  src: "/assets/audio/adrift-among-infinite-stars.mp3",
  source:
    "https://www.scottbuckley.com.au/library/adrift-among-infinite-stars/",
  license: "https://creativecommons.org/licenses/by/4.0/",
};
const STORAGE_KEY = "marsastro.music.v1";
type Preferences = { enabled: boolean; volume: number };
function loadPreferences(): Preferences {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "null");
    if (
      typeof value?.enabled === "boolean" &&
      typeof value?.volume === "number" &&
      Number.isFinite(value.volume)
    )
      return {
        enabled: value.enabled,
        volume: Math.max(0, Math.min(1, value.volume)),
      };
  } catch {
    /* Music preferences must never block a mission. */
  }
  return { enabled: true, volume: 0.24 };
}

export function useBackgroundMusic() {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [preferences, setPreferences] = useState(loadPreferences);
  const current = useRef(preferences);
  const started = useRef(false);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState("");
  const start = useCallback(() => {
    const audio = audioRef.current;
    if (!audio || !current.current.enabled || document.hidden) return;
    audio.volume = current.current.volume;
    void audio
      .play()
      .then(() => {
        started.current = true;
        setError("");
      })
      .catch((reason: unknown) => {
        // Restoring a hidden tab can require another trusted gesture.
        if (
          reason instanceof DOMException &&
          (reason.name === "NotAllowedError" || reason.name === "AbortError")
        )
          return;
        setError("Music could not load. Use the music button to retry.");
      });
  }, []);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const gesture = (event: Event) => {
      if (
        event.target instanceof Element &&
        event.target.closest("[data-music-control]")
      )
        return;
      if (
        event instanceof KeyboardEvent &&
        (event.repeat ||
          ["Shift", "Control", "Alt", "Meta", "Escape", "Tab"].includes(
            event.key,
          ))
      )
        return;
      if (audio.paused && !audio.error) start();
    };
    const resume = () => {
      if (started.current && !audio.error) start();
    };
    const pause = () => audio.pause();
    const visibility = () => {
      if (document.hidden) pause();
      else resume();
    };
    const onPlay = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    const onError = () => {
      setPlaying(false);
      setError("Music could not load. Use the music button to retry.");
    };
    document.addEventListener("pointerdown", gesture);
    document.addEventListener("pointerup", gesture);
    document.addEventListener("keydown", gesture);
    document.addEventListener("visibilitychange", visibility);
    window.addEventListener("pagehide", pause);
    window.addEventListener("pageshow", resume);
    audio.addEventListener("play", onPlay);
    audio.addEventListener("pause", onPause);
    audio.addEventListener("error", onError);
    return () => {
      document.removeEventListener("pointerdown", gesture);
      document.removeEventListener("pointerup", gesture);
      document.removeEventListener("keydown", gesture);
      document.removeEventListener("visibilitychange", visibility);
      window.removeEventListener("pagehide", pause);
      window.removeEventListener("pageshow", resume);
      audio.removeEventListener("play", onPlay);
      audio.removeEventListener("pause", onPause);
      audio.removeEventListener("error", onError);
      audio.pause();
    };
  }, [start]);

  useEffect(() => {
    current.current = preferences;
    const audio = audioRef.current;
    if (audio) {
      audio.volume = preferences.volume;
      if (!preferences.enabled) audio.pause();
    }
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
    } catch {
      /* Optional preference only. */
    }
  }, [preferences]);

  const setEnabled = (enabled: boolean) => {
    current.current = { ...current.current, enabled };
    setPreferences(current.current);
    if (enabled) {
      if (error) {
        audioRef.current?.load();
        setError("");
      }
      start();
    } else audioRef.current?.pause();
  };
  const setVolume = (volume: number) => {
    current.current = {
      ...current.current,
      volume: Math.max(0, Math.min(1, volume)),
    };
    setPreferences(current.current);
    start();
  };
  return {
    ...preferences,
    playing,
    error,
    audioRef,
    setEnabled,
    setVolume,
    toggle: () => setEnabled(error ? true : !playing),
  };
}
