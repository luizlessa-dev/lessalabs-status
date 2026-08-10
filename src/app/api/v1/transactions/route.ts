import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@/lib/supabase/server";
import type { ApiTransactionsResponse } from "@/lib/types";

function parseEWKT(ewkt: string): [number, number] | null {
  const match = ewkt.match(/POINT\(([^\s]+)\s+([^)]+)\)/);
  if (!match) return null;
  const lng = parseFloat(match[1]);
  const lat = parseFloat(match[2]);
  if (isNaN(lng) || isNaN(lat)) return null;
  return [lng, lat];
}

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;

  const cidade   = searchParams.get("cidade") ?? "belo-horizonte";
  const bairro   = searchParams.get("bairro");
  const tipo     = searchParams.get("tipo");
  const de       = searchParams.get("de");
  const ate      = searchParams.get("ate");
  const page     = Math.max(1, parseInt(searchParams.get("page") ?? "1"));
  const per_page = Math.min(500, parseInt(searchParams.get("per_page") ?? "100"));
  const offset   = (page - 1) * per_page;

  const supabase = createServerClient();

  // Resolve slug → city_id
  const { data: cityRow, error: cityErr } = await supabase
    .from("cities")
    .select("id")
    .eq("slug", cidade)
    .single();

  if (cityErr || !cityRow) {
    return NextResponse.json({ error: `Cidade '${cidade}' não encontrada.` }, { status: 404 });
  }

  let query = supabase
    .from("transactions")
    .select(
      `id, city_id, address, neighborhood, value, area_m2, price_m2,
       property_type, transaction_date, source,
       geom:geom::text`,
      { count: "exact" }
    )
    .eq("city_id", cityRow.id)
    .not("geom", "is", null)
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

  const features = (data ?? []).flatMap((row) => {
    const coords = row.geom ? parseEWKT(row.geom as string) : null;
    if (!coords) return [];
    const { geom: _g, ...props } = row;
    return [{
      type: "Feature" as const,
      geometry: { type: "Point" as const, coordinates: coords },
      properties: props,
    }];
  });

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
