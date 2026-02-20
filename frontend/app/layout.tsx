import "./globals.css";
import type { ReactNode } from "react";
import { Noto_Nastaliq_Urdu } from "next/font/google";

export const metadata = {
  title: "Urdu Story Generator",
  description: "Generate Urdu stories from a starting phrase.",
};

const urduFont = Noto_Nastaliq_Urdu({
  subsets: ["arabic"],
  weight: "400",
});

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ur" dir="rtl">
      <body className={urduFont.className}>{children}</body>
    </html>
  );
}

