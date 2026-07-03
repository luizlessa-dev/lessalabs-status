import type { City } from "@/lib/types";

export const CITIES: Record<string, City> = {
  "sao-paulo": {
    slug: "sao-paulo",
    name: "São Paulo",
    uf: "SP",
    center: [-46.6333, -23.5505],
    zoom: 11,
  },
  "rio-de-janeiro": {
    slug: "rio-de-janeiro",
    name: "Rio de Janeiro",
    uf: "RJ",
    center: [-43.1729, -22.9068],
    zoom: 11,
  },
  "belo-horizonte": {
    slug: "belo-horizonte",
    name: "Belo Horizonte",
    uf: "MG",
    center: [-43.9378, -19.9208],
    zoom: 12,
  },
  "porto-alegre": {
    slug: "porto-alegre",
    name: "Porto Alegre",
    uf: "RS",
    center: [-51.2177, -30.0346],
    zoom: 12,
  },
};

export const DEFAULT_CITY = CITIES["sao-paulo"];
