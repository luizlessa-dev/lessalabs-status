"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { CITIES, DEFAULT_CITY } from "@/data/cities";
import type { TransactionFeature } from "@/lib/types";
import type { Filters } from "@/components/FilterPanel";
import TransactionPopup from "./TransactionPopup";

type Props = { citySlug: string; filters?: Filters };

const TILE_URL = "https://tiles.openfreemap.org/styles/liberty";

export default function MapView({ citySlug, filters = {} }: Props) {
  const mapRef = useRef<maplibregl.Map | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const mapReadyRef = useRef(false);
  const [selected, setSelected] = useState<TransactionFeature | null>(null);
  const [loading, setLoading] = useState(false);
  const [count, setCount] = useState<number | null>(null);

  const city = CITIES[citySlug] ?? DEFAULT_CITY;
  const { tipo, de, ate, bairro } = filters;

  // Initialise map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: TILE_URL,
      center: city.center,
      zoom: city.zoom,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");

    map.on("load", () => {
      map.addSource("transactions", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 40,
      });

      map.addLayer({
        id: "clusters",
        type: "circle",
        source: "transactions",
        filter: ["has", "point_count"],
        paint: {
          "circle-color": [
            "step", ["get", "point_count"],
            "#1A5CFF", 50, "#009E88", 200, "#E07B00",
          ],
          "circle-radius": [
            "step", ["get", "point_count"],
            16, 50, 22, 200, 30,
          ],
          "circle-opacity": 0.85,
        },
      });

      map.addLayer({
        id: "cluster-count",
        type: "symbol",
        source: "transactions",
        filter: ["has", "point_count"],
        layout: {
          "text-field": "{point_count_abbreviated}",
          "text-size": 12,
          "text-font": ["Noto Sans Bold"],
        },
        paint: { "text-color": "#fff" },
      });

      map.addLayer({
        id: "unclustered-point",
        type: "circle",
        source: "transactions",
        filter: ["!", ["has", "point_count"]],
        paint: {
          "circle-color": "#1A5CFF",
          "circle-radius": 7,
          "circle-stroke-width": 2,
          "circle-stroke-color": "#fff",
          "circle-opacity": 0.9,
        },
      });

      mapReadyRef.current = true;
      fetchAndLoad(map, citySlug, filters, setLoading, setCount);
    });

    map.on("click", "unclustered-point", (e) => {
      const feature = e.features?.[0] as unknown as TransactionFeature;
      if (!feature) return;
      setSelected(feature);
    });

    map.on("click", "clusters", async (e) => {
      const features = map.queryRenderedFeatures(e.point, { layers: ["clusters"] });
      const clusterId = features[0].properties?.cluster_id;
      const source = map.getSource("transactions") as maplibregl.GeoJSONSource;
      const zoom = await source.getClusterExpansionZoom(clusterId);
      map.easeTo({
        center: (features[0].geometry as GeoJSON.Point).coordinates as [number, number],
        zoom: zoom ?? map.getZoom() + 2,
      });
    });

    map.getCanvas().style.cursor = "default";
    map.on("mouseenter", "unclustered-point", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "unclustered-point", () => { map.getCanvas().style.cursor = ""; });
    map.on("mouseenter", "clusters", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "clusters", () => { map.getCanvas().style.cursor = ""; });

    mapRef.current = map;
    return () => {
      mapReadyRef.current = false;
      map.remove();
      mapRef.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Reload on city or filter change (only after map is ready)
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReadyRef.current) return;
    map.easeTo({ center: city.center, zoom: city.zoom, duration: 800 });
    fetchAndLoad(map, citySlug, filters, setLoading, setCount);
  }, [citySlug, city.center, city.zoom, tipo, de, ate, bairro]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleClose = useCallback(() => setSelected(null), []);

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full" />

      {/* Loading overlay */}
      {loading && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 pointer-events-none">
          <div className="bg-white/90 dark:bg-gray-900/90 rounded-full px-4 py-1.5 text-xs text-gray-600 dark:text-gray-300 shadow-md flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
            Carregando dados…
          </div>
        </div>
      )}

      {/* Record count badge */}
      {!loading && count !== null && (
        <div className="absolute top-3 left-3 pointer-events-none">
          <div className="bg-white/90 dark:bg-gray-900/90 rounded-full px-3 py-1 text-xs text-gray-500 dark:text-gray-400 shadow">
            {count.toLocaleString("pt-BR")} transações
          </div>
        </div>
      )}

      {selected && (
        <TransactionPopup feature={selected} onClose={handleClose} />
      )}
    </div>
  );
}

async function fetchAndLoad(
  map: maplibregl.Map,
  citySlug: string,
  filters: Filters,
  setLoading: (v: boolean) => void,
  setCount: (n: number) => void,
) {
  setLoading(true);
  try {
    const params = new URLSearchParams({ cidade: citySlug, per_page: "1000" });
    if (filters.tipo)   params.set("tipo", filters.tipo);
    if (filters.de)     params.set("de", filters.de);
    if (filters.ate)    params.set("ate", filters.ate);
    if (filters.bairro) params.set("bairro", filters.bairro);

    const res = await fetch(`/api/v1/transactions?${params}`);
    if (!res.ok) return;
    const json = await res.json();

    const source = map.getSource("transactions") as maplibregl.GeoJSONSource | undefined;
    source?.setData({ type: "FeatureCollection", features: json.data ?? [] });
    setCount(json.total ?? json.data?.length ?? 0);
  } finally {
    setLoading(false);
  }
}
