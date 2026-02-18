"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";

const SIZES = ["font-sm", "font-md", "font-lg"] as const;
const LABELS = ["A", "Aa", "AA"] as const;

export function FontSizeToggle() {
  const [sizeIdx, setSizeIdx] = useState(1);

  useEffect(() => {
    const stored = localStorage.getItem("font-size");
    if (stored) {
      const idx = SIZES.indexOf(stored as (typeof SIZES)[number]);
      if (idx >= 0) setSizeIdx(idx);
    }
  }, []);

  useEffect(() => {
    const html = document.documentElement;
    SIZES.forEach((s) => html.classList.remove(s));
    html.classList.add(SIZES[sizeIdx]);
    localStorage.setItem("font-size", SIZES[sizeIdx]);
  }, [sizeIdx]);

  function cycle() {
    setSizeIdx((prev) => (prev + 1) % SIZES.length);
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={cycle}
      aria-label={`Font size: ${LABELS[sizeIdx]}`}
      title={`Font size: ${LABELS[sizeIdx]}`}
    >
      <span className="text-sm font-serif font-bold">{LABELS[sizeIdx]}</span>
    </Button>
  );
}
