import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Quasar Sage",
  description: "An elite AI Chief Revenue Officer, built as a teaching tool for sales & marketing methodology.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
