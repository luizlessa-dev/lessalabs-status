import { Suspense } from "react";
import CitySelector from "@/components/CitySelector";
import Header from "@/components/Header";
import MapSection from "@/components/MapSection";

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ cidade?: string }>;
}) {
  const { cidade = "belo-horizonte" } = await searchParams;

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header />
      <MapSection
        citySlug={cidade}
        citySelectorSlot={
          <Suspense>
            <CitySelector searchParams={searchParams} />
          </Suspense>
        }
      />
    </div>
  );
}
