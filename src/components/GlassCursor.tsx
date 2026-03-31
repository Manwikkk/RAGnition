import React, { useEffect, useRef, useState } from "react";

export default function GlassCursor() {
  const cursorRef = useRef<HTMLDivElement | null>(null);
  const rafRef = useRef<number | null>(null);
  const targetPos = useRef({ x: -100, y: -100 });
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches ?? false;
    const finePointer = window.matchMedia?.("(pointer: fine)")?.matches ?? false;
    if (!finePointer || reduceMotion) return;
    setEnabled(true);
  }, []);

  useEffect(() => {
    if (!enabled) return;
    const cursorEl = cursorRef.current;
    if (!cursorEl) return;

    const isInteractiveTarget = (el: EventTarget | null) => {
      const node = el as HTMLElement | null;
      if (!node) return false;
      if (node.closest("button, a, input, textarea, select, [role='button']")) return true;
      if (node.closest(".glass-card-hover, .glass-subtle, .glass-card")) return true;
      return false;
    };

    const onMove = (e: MouseEvent) => {
      targetPos.current = { x: e.clientX, y: e.clientY };
      if (rafRef.current != null) return;

      rafRef.current = window.requestAnimationFrame(() => {
        rafRef.current = null;
        cursorEl.style.transform = `translate(${targetPos.current.x}px, ${targetPos.current.y}px)`;
      });
      cursorEl.classList.add("glass-cursor--visible");
    };

    const onMouseOver = (e: MouseEvent) => {
      const active = isInteractiveTarget(e.target);
      cursorEl.classList.toggle("glass-cursor--active", active);
      cursorEl.classList.add("glass-cursor--visible");
    };

    const onMouseOut = () => {
      cursorEl.classList.remove("glass-cursor--active");
      // Keep it visible so it follows the cursor everywhere.
    };

    window.addEventListener("mousemove", onMove, { passive: true });
    window.addEventListener("mouseover", onMouseOver as any);
    window.addEventListener("mouseout", onMouseOut as any);

    return () => {
      if (rafRef.current != null) window.cancelAnimationFrame(rafRef.current);
      window.removeEventListener("mousemove", onMove as any);
      window.removeEventListener("mouseover", onMouseOver as any);
      window.removeEventListener("mouseout", onMouseOut as any);
    };
  }, [enabled]);

  if (!enabled) return null;
  return <div ref={cursorRef} className="glass-cursor glass-cursor--visible" aria-hidden="true" />;
}

