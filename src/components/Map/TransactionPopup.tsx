"use client";

import type { TransactionFeature } from "@/lib/types";
import { formatCurrency, formatDate } from "@/lib/utils";

type Props = {
  feature: TransactionFeature;
  onClose: () => void;
};

const TYPE_LABELS: Record<string, string> = {
  residential: "Residencial",
  commercial:  "Comercial",
  land:        "Terreno",
};

export default function TransactionPopup({ feature, onClose }: Props) {
  const p = feature.properties;

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-10 w-80 bg-[var(--surface)] rounded-xl border border-[var(--border)] shadow-xl overflow-hidden">
      <div className="flex items-start justify-between px-4 pt-4 pb-2">
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--muted)]">
            {p.neighborhood ?? "—"} · {p.transaction_date ? formatDate(p.transaction_date) : "—"}
          </p>
          <p className="text-sm font-medium text-[var(--foreground)] mt-0.5 leading-snug">
            {p.address}
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-[var(--muted)] hover:text-[var(--foreground)] ml-2 mt-0.5 text-lg leading-none"
          aria-label="Fechar"
        >
          ×
        </button>
      </div>

      <div className="grid grid-cols-3 gap-px bg-[var(--border)] border-t border-[var(--border)]">
        <Stat
          label="Valor"
          value={p.value ? formatCurrency(p.value) : "—"}
          highlight
        />
        <Stat
          label="Área"
          value={p.area_m2 ? `${p.area_m2} m²` : "—"}
        />
        <Stat
          label="R$/m²"
          value={p.price_m2 ? formatCurrency(p.price_m2) : "—"}
        />
      </div>

      {p.property_type && (
        <div className="px-4 py-2.5 border-t border-[var(--border)]">
          <span className="inline-block text-xs font-semibold bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 px-2 py-0.5 rounded-full">
            {TYPE_LABELS[p.property_type] ?? p.property_type}
          </span>
          <span className="ml-2 text-xs text-[var(--muted)] font-mono">{p.source}</span>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="bg-[var(--surface)] px-3 py-2.5">
      <p className="text-[10px] font-bold uppercase tracking-widest text-[var(--muted)]">{label}</p>
      <p className={["text-sm font-bold tabular-nums", highlight ? "text-[var(--accent)]" : "text-[var(--foreground)]"].join(" ")}>
        {value}
      </p>
    </div>
  );
}
