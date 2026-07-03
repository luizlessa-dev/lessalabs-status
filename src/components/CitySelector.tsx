import Link from "next/link";
import { CITIES } from "@/data/cities";

const DATA_SOURCES: Record<string, { period: string; source: string }> = {
  "sao-paulo":      { period: "2019–hoje", source: "Sec. Municipal da Fazenda SP" },
  "rio-de-janeiro": { period: "2010–hoje", source: "data.rio / ArcGIS" },
  "belo-horizonte": { period: "2008–hoje", source: "Portal de Dados Abertos PBH" },
  "porto-alegre":   { period: "2020–hoje", source: "dadosabertos.poa.br" },
};

export default async function CitySelector({
  searchParams,
}: {
  searchParams: Promise<{ cidade?: string }>;
}) {
  const { cidade = "sao-paulo" } = await searchParams;

  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs font-bold uppercase tracking-widest text-[var(--muted)] mb-1">
        Cidades
      </p>
      {Object.values(CITIES).map((city) => {
        const active = cidade === city.slug;
        const meta = DATA_SOURCES[city.slug];
        return (
          <Link
            key={city.slug}
            href={`/?cidade=${city.slug}`}
            className={[
              "rounded-lg px-3 py-2.5 border transition-all",
              active
                ? "border-[var(--accent)] bg-blue-50 dark:bg-blue-950/30"
                : "border-[var(--border)] hover:border-[var(--accent)]/50",
            ].join(" ")}
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-sm text-[var(--foreground)]">
                {city.name}
              </span>
              <span className="text-xs font-mono text-[var(--muted)]">{city.uf}</span>
            </div>
            {meta && (
              <div className="mt-1 text-xs text-[var(--muted)]">
                {meta.period} · {meta.source}
              </div>
            )}
          </Link>
        );
      })}

      <div className="mt-4 pt-4 border-t border-[var(--border)]">
        <p className="text-xs text-[var(--muted)] leading-relaxed">
          Dados públicos das prefeituras. Sem cadastro, sem paywall.
        </p>
      </div>
    </div>
  );
}
