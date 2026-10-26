import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "SmartGrocery",
    template: "%s | SmartGrocery",
  },

  description:
    "SmartGrocery - Intelligent Grocery E-Commerce Platform",

  keywords: [
    "SmartGrocery",
    "Grocery",
    "E-Commerce",
    "Inventory Management",
    "Demand Forecasting",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}