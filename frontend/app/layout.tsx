import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono, Fraunces } from "next/font/google";
import "./globals.css";
import { TenantProvider } from "../providers/TenantProvider";
import { Toaster } from "@/components/ui/sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "DukanYar — aap dukan sambhalein, hisaab hum",
  description:
    "Aap bolen, DukanYar sunta hai aur khata rakh deta hai. Voice-first hisaab-kitaab for kiryana shopkeepers.",
};

export const viewport: Viewport = {
  themeColor: "#2c6e49",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${fraunces.variable} antialiased`}
      >
        <TenantProvider value={{ currentUser: null, currentShop: null }}>
          {children}
        </TenantProvider>
        <Toaster position="top-center" />
      </body>
    </html>
  );
}
