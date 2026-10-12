import { Fragment } from "react";

/**
 * Renders the tiny markdown subset used by curriculum content — **bold** and *italic* —
 * as React nodes (no HTML injection).
 */
export function RichText({ text, className }: { text: string; className?: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g).filter(Boolean);
  return (
    <span className={className}>
      {parts.map((p, i) =>
        p.startsWith("**") ? (
          <strong key={i} className="font-extrabold text-ink-900">
            {p.slice(2, -2)}
          </strong>
        ) : p.startsWith("*") && p.length > 2 ? (
          <em key={i} className="not-italic underline decoration-curio-300 decoration-2 underline-offset-2">
            {p.slice(1, -1)}
          </em>
        ) : (
          <Fragment key={i}>{p}</Fragment>
        ),
      )}
    </span>
  );
}
