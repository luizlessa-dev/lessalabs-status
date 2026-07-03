export type City = {
  slug: string;
  name: string;
  uf: string;
  center: [number, number]; // [lng, lat]
  zoom: number;
};

export type Transaction = {
  id: number;
  city_id: number;
  address: string;
  neighborhood: string | null;
  zip_code: string | null;
  value: number;
  area_m2: number | null;
  price_m2: number | null;
  property_type: "residential" | "commercial" | "land" | null;
  transaction_date: string;
  source: string;
  geom: { type: "Point"; coordinates: [number, number] } | null;
};

export type TransactionFeature = {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] };
  properties: Omit<Transaction, "geom">;
};

export type NeighborhoodStats = {
  neighborhood: string;
  city_id: number;
  avg_price_m2: number;
  transaction_count: number;
  period_start: string;
  period_end: string;
};

export type ApiTransactionsResponse = {
  data: TransactionFeature[];
  total: number;
  page: number;
  per_page: number;
};
