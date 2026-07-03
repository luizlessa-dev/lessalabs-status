"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { CITIES, DEFAULT_CITY } from "@/data/cities";
import type { TransactionFeature } from "@/lib/types";
import TransactionPopup from "./TransactionPopup";

type Props = { citySlug: string };

const TILE_URL = "https://tiles.openfreemap.org/styles/liberty";

export default function MapView({ citySlug }: Props) {
  const mapRef = useRef<maplibregl.Map | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const [selected, setSelected] = useState<TransactionFeature | null>(null);

  const city = CITIES[citySlug] ?? DEFAULT_CITY;

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

      loadTransactions(map, citySlug);
    });

    map.on("click", "unclustered-point", (e) => {
      const feature = e.features?.[0] as unknown as TransactionFeature;
      if (!feature) return;
      setSelected(feature);
    });

    map.on("click", "clusters", (e) => {
      const features = map.queryRenderedFeatures(e.point, { layers: ["clusters"] });
      const clusterId = features[0].properties?.cluster_id;
      (map.getSource("transactions") as maplibregl.GeoJSONSource)
        .getClusterExpansionZoom(clusterId, (err, zoom) => {
          if (err) return;
          map.easeTo({
            center: (features[0].geometry as GeoJSON.Point).coordinates as [number, number],
            zoom: zoom ?? map.getZoom() + 2,
          });
        });
    });

    map.getCanvas().style.cursor = "default";
    map.on("mouseenter", "unclustered-point", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "unclustered-point", () => { map.getCanvas().style.cursor = ""; });
    map.on("mouseenter", "clusters", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "clusters", () => { map.getCanvas().style.cursor = ""; });

    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    map.easeTo({ center: city.center, zoom: city.zoom, duration: 800 });
    loadTransactions(map, citySlug);
  }, [citySlug, city.center, city.zoom]);

  const handleClose = useCallback(() => setSelected(null), []);

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full" />
      {selected && (
        <TransactionPopup feature={selected} onClose={handleClose} />
      )}
    </div>
  );
}

async function loadTransactions(map: maplibregl.Map, citySlug: string) {
  const params = new URLSearchParams({ cidade: citySlug, per_page: "500" });
  const res = await fetch(`/api/v1/transactions?${params}`);
  if (!res.ok) return;
  const json = await res.json();
  const source = map.getSource("transactions") as maplibregl.GeoJSONSource | undefined;
  source?.setData({ type: "FeatureCollection", features: json.data });
}
