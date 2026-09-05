"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import FilterPanel, { type Filters } from "./FilterPanel";
import { CITIES } from "@/data/cities";

const MapView = dynamic(() => import("./Map/MapView"), {
  ssr: false,
  loading: () => <div className="w-full h-full bg-[var(--background)] animate-pulse" />,
});

type Props = {
  citySlug: string;
  citySelectorSlot: React.ReactNode;
};

export default function MapSection({ citySlug, citySelectorSlot }: Props) {
  const [filters, setFilters] = useState<Filters>({});
  const router = useRouter();

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Mobile: city select + filters in a compact top bar */}
      <div className="lg:hidden w-full absolute top-0 left-0 z-10 bg-[var(--surface)] border-b border-[var(--border)] px-3 py-2 flex gap-2">
        <select
          value={citySlug}
          onChange={(e) => router.push(`/?cidade=${e.target.value}`)}
          className="flex-1 rounded-md border border-[var(--border)] bg-[var(--background)] px-2 py-1.5 text-sm text-[var(--foreground)] focus:outline-none"
        >
          {Object.values(CITIES).map((c) => (
            <option key={c.slug} value={c.slug}>
              {c.name}
            </option>
          ))}
        </select>
        <select
          value={filters.tipo ?? ""}
          onChange={(e) =>
            setFilters((f) => ({ ...f, tipo: e.target.value || undefined }))
          }
          className="rounded-md border border-[var(--border)] bg-[var(--background)] px-2 py-1.5 text-sm text-[var(--foreground)] focus:outline-none"
        >
          <option value="">Todos</option>
          <option value="residential">Residencial</option>
          <option value="commercial">Comercial</option>
          <option value="land">Terreno</option>
        </select>
      </div>

      {/* Desktop sidebar */}
      <aside className="hidden lg:block w-72 shrink-0 border-r border-[var(--border)] bg-[var(--surface)] overflow-y-auto p-4">
        {citySelectorSlot}
        <FilterPanel filters={filters} onChange={setFilters} />
      </aside>

      {/* Map */}
      <main className="flex-1 relative lg:pt-0 pt-12">
        <MapView citySlug={citySlug} filters={filters} />
      </main>
    </div>
  );
}
