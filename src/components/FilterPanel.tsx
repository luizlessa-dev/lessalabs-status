"use client";

export type Filters = {
  tipo?: string;
  de?: string;
  ate?: string;
  bairro?: string;
};

type Props = {
  filters: Filters;
  onChange: (filters: Filters) => void;
};

const TIPOS = [
  { value: "", label: "Todos os tipos" },
  { value: "residential", label: "Residencial" },
  { value: "commercial", label: "Comercial" },
  { value: "land", label: "Terreno" },
];

export default function FilterPanel({ filters, onChange }: Props) {
  const set = (key: keyof Filters, value: string) =>
    onChange({ ...filters, [key]: value || undefined });

  const hasFilters = Object.values(filters).some(Boolean);

  return (
    <div className="mt-5 pt-4 border-t border-[var(--border)]">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-bold uppercase tracking-widest text-[var(--muted)]">
          Filtros
        </p>
        {hasFilters && (
          <button
            onClick={() => onChange({})}
            className="text-xs text-[var(--accent)] hover:underline"
          >
            Limpar
          </button>
        )}
      </div>

      <div className="flex flex-col gap-3">
        <div>
          <label className="block text-xs text-[var(--muted)] mb-1">Bairro</label>
          <input
            type="text"
            placeholder="Ex: Savassi"
            value={filters.bairro ?? ""}
            onChange={(e) => set("bairro", e.target.value)}
            className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-2.5 py-1.5 text-sm text-[var(--foreground)] placeholder-[var(--muted)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]"
          />
        </div>

        <div>
          <label className="block text-xs text-[var(--muted)] mb-1">Tipo</label>
          <select
            value={filters.tipo ?? ""}
            onChange={(e) => set("tipo", e.target.value)}
            className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-2.5 py-1.5 text-sm text-[var(--foreground)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]"
          >
            {TIPOS.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs text-[var(--muted)] mb-1">Período</label>
          <div className="flex items-center gap-1.5">
            <input
              type="date"
              value={filters.de ?? ""}
              onChange={(e) => set("de", e.target.value)}
              className="flex-1 min-w-0 rounded-md border border-[var(--border)] bg-[var(--background)] px-2 py-1.5 text-xs text-[var(--foreground)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]"
            />
            <span className="text-[var(--muted)] text-xs shrink-0">até</span>
            <input
              type="date"
              value={filters.ate ?? ""}
              onChange={(e) => set("ate", e.target.value)}
              className="flex-1 min-w-0 rounded-md border border-[var(--border)] bg-[var(--background)] px-2 py-1.5 text-xs text-[var(--foreground)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
