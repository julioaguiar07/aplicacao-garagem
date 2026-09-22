import type { Metadata } from "next";
import { Archivo, Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

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

const DESCRICAO =
  "Seminovos revisados e com procedência na Carmelo Multimarcas, em Mossoró/RN. Veja o estoque, simule o financiamento e fale com a gente pelo WhatsApp.";

export const metadata: Metadata = {
  metadataBase: new URL("https://www.carmelomultimarcas.com.br"),
  title: {
    default: "Carmelo Multimarcas | Seminovos com procedência em Mossoró/RN",
    template: "%s | Carmelo Multimarcas",
  },
  description: DESCRICAO,
  applicationName: "Carmelo Multimarcas",
  openGraph: {
    type: "website",
    locale: "pt_BR",
    siteName: "Carmelo Multimarcas",
    title: "Carmelo Multimarcas | Seminovos com procedência em Mossoró/RN",
    description: DESCRICAO,
    images: [{ url: "/marca/compartilhar.png", width: 1200, height: 630, alt: "Carmelo Multimarcas" }],
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="pt-BR"
      className={`${archivo.variable} ${geist.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full">{children}</body>
    </html>
  );
}
