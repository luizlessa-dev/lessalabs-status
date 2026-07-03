import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@/lib/supabase/server";
import type { ApiTransactionsResponse } from "@/lib/types";

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;

  const cidade   = searchParams.get("cidade") ?? "sao-paulo";
  const bairro   = searchParams.get("bairro");
  const tipo     = searchParams.get("tipo");
  const de       = searchParams.get("de");
  const ate      = searchParams.get("ate");
  const page     = Math.max(1, parseInt(searchParams.get("page") ?? "1"));
  const per_page = Math.min(500, parseInt(searchParams.get("per_page") ?? "100"));
  const offset   = (page - 1) * per_page;

  // Bounding box para query espacial (opcional)
  const bbox = searchParams.get("bbox"); // "lng1,lat1,lng2,lat2"

  const supabase = createServerClient();

  let query = supabase
    .from("transactions")
    .select(
      `id, city_id, address, neighborhood, zip_code, value, area_m2, price_m2,
       property_type, transaction_date, source,
       geom:geom::text`,
      { count: "exact" }
    )
    .eq("cities.slug", cidade)
    .order("transaction_date", { ascending: false })
    .range(offset, offset + per_page - 1);

  if (bairro) query = query.ilike("neighborhood", `%${bairro}%`);
  if (tipo)   query = query.eq("property_type", tipo);
  if (de)     query = query.gte("transaction_date", de);
  if (ate)    query = query.lte("transaction_date", ate);

  const { data, error, count } = await query;

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  const features = (data ?? []).map((row) => {
    let coords: [number, number] | null = null;
    if (row.geom) {
      try {
        const g = JSON.parse(row.geom);
        coords = g.coordinates;
      } catch {
        coords = null;
      }
    }
    const { geom: _g, ...props } = row;
    return {
      type: "Feature" as const,
      geometry: coords
        ? { type: "Point" as const, coordinates: coords }
        : { type: "Point" as const, coordinates: [0, 0] as [number, number] },
      properties: props,
    };
  }).filter((f) => f.geometry.coordinates[0] !== 0);

  const response: ApiTransactionsResponse = {
    data: features,
    total: count ?? 0,
    page,
    per_page,
  };

  return NextResponse.json(response, {
    headers: {
      "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600",
      "Access-Control-Allow-Origin": "*",
    },
  });
}
