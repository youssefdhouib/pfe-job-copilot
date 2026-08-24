import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geist = Geist({ variable: "--font-geist", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "PFE Job Copilot",
  description: "Collect, rank, and track PFE internship opportunities from one focused queue.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${geist.variable} ${geistMono.variable}`}>
      <body>
        {/*
        THESIS: A working search dossier turns scattered offers into evidence; it refuses the generic metric-card dashboard.
        OWN-WORLD: Chalk paper, carbon ink, cobalt annotations, ruled structure, and a vertical relevance ruler organize the queue.
        STORY: See what arrived, isolate the strongest matches, inspect the evidence, and advance the next application.
        FIRST VIEWPORT: A compact masthead and stage index frame a dense two-column queue with collection controls at hand.
        FORM: Engineering lab notebook, grounded direction 4, seed 353ecd12.
        FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and DESIGN.md
        */}
        {children}
      </body>
    </html>
  );
}
