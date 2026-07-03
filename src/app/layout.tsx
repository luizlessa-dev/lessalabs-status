import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ValorReal — Preços reais de imóveis no Brasil",
  description:
    "Mapa público de transações imobiliárias em São Paulo, Rio de Janeiro, Belo Horizonte e Porto Alegre. Dados abertos das prefeituras.",
  openGraph: {
    title: "ValorReal",
    description: "O preço real dos imóveis no Brasil",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className="antialiased">{children}</body>
    </html>
  );
}
