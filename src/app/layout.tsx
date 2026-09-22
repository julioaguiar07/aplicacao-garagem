import type { Metadata } from "next";
import { Archivo, Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { SeloDemo } from "@/components/selo-demo";
import { DEMO, MARCA, logo } from "@/lib/marca";

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
  axes: ["wdth"],
});

const geist = Geist({
  variable: "--font-geist",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const TITULO = `${MARCA.nome} | ${MARCA.slogan}`;

export const metadata: Metadata = {
  ...(MARCA.site ? { metadataBase: new URL(MARCA.site) } : {}),
  title: { default: TITULO, template: `%s | ${MARCA.nome}` },
  description: MARCA.descricao,
  applicationName: MARCA.nome,
  icons: {
    icon: [
      { url: logo("favicon.ico"), sizes: "48x48" },
      { url: logo("icon.png"), sizes: "512x512", type: "image/png" },
    ],
    apple: { url: logo("apple-icon.png"), sizes: "180x180" },
  },
  openGraph: {
    type: "website",
    locale: "pt_BR",
    siteName: MARCA.nome,
    title: TITULO,
    description: MARCA.descricao,
    images: [{ url: logo("compartilhar.png"), width: 1200, height: 630, alt: MARCA.nome }],
  },
  // A demonstração não aparece no Google
  ...(DEMO ? { robots: { index: false, follow: false } } : {}),
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="pt-BR"
      className={`${archivo.variable} ${geist.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full">
        <SeloDemo />
        {children}
      </body>
    </html>
  );
}
