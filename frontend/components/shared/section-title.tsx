export function SectionTitle({ emoji, children, action }: { emoji?: React.ReactNode; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
      <h2 className="flex items-center gap-2 text-lg font-black text-ink-900">
        {emoji}
        {children}
      </h2>
      {action}
    </div>
  );
}
