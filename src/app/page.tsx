import { Suspense } from "react";
import MapView from "@/components/Map/MapView";
import CitySelector from "@/components/CitySelector";
import Header from "@/components/Header";

export default function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ cidade?: string }>;
}) {
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-72 shrink-0 border-r border-[var(--border)] bg-[var(--surface)] overflow-y-auto hidden lg:block p-4">
          <Suspense>
            <CitySelector searchParams={searchParams} />
          </Suspense>
        </aside>
        <main className="flex-1 relative">
          <Suspense fallback={<div className="w-full h-full bg-[var(--background)] animate-pulse" />}>
            <MapViewWrapper searchParams={searchParams} />
          </Suspense>
        </main>
      </div>
    </div>
  );
}

async function MapViewWrapper({
  searchParams,
}: {
  searchParams: Promise<{ cidade?: string }>;
}) {
  const { cidade = "sao-paulo" } = await searchParams;
  return <MapView citySlug={cidade} />;
}
