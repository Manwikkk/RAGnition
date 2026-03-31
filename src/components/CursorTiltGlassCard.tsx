import React, { useEffect, useRef, useState } from "react";
import { motion, useMotionValue, useSpring } from "framer-motion";

interface CursorTiltGlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
  children: React.ReactNode;
  intensity?: number; // tilt intensity multiplier
}

export default function CursorTiltGlassCard({
  className,
  children,
  intensity = 1,
  ...rest
}: CursorTiltGlassCardProps) {
  const cardRef = useRef<HTMLDivElement | null>(null);
  const [enabled, setEnabled] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const rotateX = useSpring(useMotionValue(0), { stiffness: 180, damping: 20, mass: 0.5 });
  const rotateY = useSpring(useMotionValue(0), { stiffness: 180, damping: 20, mass: 0.5 });
  const glareX = useRef(50);
  const glareY = useRef(50);
  const glareRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches ?? false;
    const finePointer = window.matchMedia?.("(pointer: fine)")?.matches ?? false;
    setEnabled(finePointer && !reduceMotion);
  }, []);

  const handleMove: React.MouseEventHandler<HTMLDivElement> = (e) => {
    if (!enabled) return;
    const el = cardRef.current;
    if (!el) return;

    const rect = el.getBoundingClientRect();
    const px = Math.min(Math.max((e.clientX - rect.left) / rect.width, 0), 1);
    const py = Math.min(Math.max((e.clientY - rect.top) / rect.height, 0), 1);

    // Update CSS vars for glare/reflection gradient
    el.style.setProperty("--mx", `${px * 100}%`);
    el.style.setProperty("--my", `${py * 100}%`);

    glareX.current = px * 100;
    glareY.current = py * 100;

    if (glareRef.current) {
      glareRef.current.style.background = `
        radial-gradient(
          ellipse 80% 60% at ${glareX.current}% ${glareY.current}%,
          rgba(255,255,255,0.28) 0%,
          rgba(255,255,255,0.10) 30%,
          rgba(120,100,255,0.06) 55%,
          transparent 75%
        )
      `;
    }

    const dx = px - 0.5;
    const dy = py - 0.5;

    rotateX.set(-dy * 14 * intensity);
    rotateY.set(dx * 16 * intensity);
  };

  const handleEnter = () => setIsHovered(true);

  const handleLeave = () => {
    setIsHovered(false);
    rotateX.set(0);
    rotateY.set(0);
    if (glareRef.current) {
      glareRef.current.style.background =
        "radial-gradient(ellipse 60% 50% at 50% 50%, rgba(255,255,255,0.08) 0%, transparent 70%)";
    }
  };

  return (
    <motion.div
      ref={cardRef}
      className={`cursor-tilt ${className || ""}`.trim()}
      onMouseMove={handleMove}
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
      style={{
        transformStyle: "preserve-3d",
        perspective: 900,
        rotateX,
        rotateY,
        position: "relative",
      }}
      {...(rest as any)}
    >
      {/* Glass shimmer layer — pointer-events: none so clicks pass through to children */}
      <div
        ref={glareRef}
        className="tilt-reflection"
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: "-1px",
          zIndex: 0,
          pointerEvents: "none",
          borderRadius: "inherit",
          background:
            "radial-gradient(ellipse 60% 50% at 50% 50%, rgba(255,255,255,0.08) 0%, transparent 70%)",
          transition: isHovered ? "none" : "background 0.6s ease",
          transform: "translateZ(1px)",
        }}
      />

      {/* Border shimmer */}
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          zIndex: 0,
          pointerEvents: "none",
          borderRadius: "inherit",
          background:
            "linear-gradient(135deg, rgba(255,255,255,0.12) 0%, transparent 40%, rgba(140,100,255,0.08) 100%)",
          maskImage:
            "linear-gradient(white, white), linear-gradient(white, white)",
          WebkitMask:
            "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
          WebkitMaskComposite: "xor",
          maskComposite: "exclude",
          padding: "1px",
        }}
      />

      {/* Children — z-index: 1 so they sit above effects but still receive pointer events */}
      <div style={{ position: "relative", zIndex: 1, width: "100%", height: "100%" }}>
        {children}
      </div>
    </motion.div>
  );
}
