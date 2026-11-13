"use client";

import { motion } from "motion/react";
import * as Accordion from "@radix-ui/react-accordion";
import { ChevronDown } from "lucide-react";

const FAQ_ITEMS = [
  {
    q: "Apakah skor tinggi membuktikan bahwa akun tersebut pasti buzzer bayaran?",
    a: "Tidak. NEXANTARA mengukur anomali koordinasi statistik dan pola kemiripan bot. Skor tinggi memerlukan tinjauan konteks oleh manusia untuk membedakan antara astroturfing bayaran dengan gerakan aktivisme organik masyarakat.",
  },
  {
    q: "Bagaimana NEXANTARA menangani bahasa gaul, singkatan, dan emoji Indonesia?",
    a: "Pra-pemrosesan teks menormalisasi karakter berulang, mengganti tautan dan mention dengan token, serta mengubah emoji menjadi deskriptor teks bahasa Indonesia tanpa menghapusnya.",
  },
  {
    q: "Mengapa sistem membatasi analisis hingga 500 cuitan per tautan?",
    a: "Batas 500 cuitan teratas membantu menyeimbangkan waktu pemrosesan dengan cakupan sinyal interaksi yang relevan dari postingan target.",
  },
  {
    q: "Data apa saja yang dikumpulkan oleh sistem NEXANTARA?",
    a: "Hanya cuitan publik dan metadata akun terbuka yang dapat diakses publik (pengikut, yang diikuti, status, bio). Tidak ada data pribadi rahasia atau pesan langsung (DM) yang disimpan.",
  },
  {
    q: "Apakah NEXANTARA bisa dihubungkan ke model backend Python khusus?",
    a: "Ya. Atur FASTAPI_BACKEND_URL pada environment variable, lalu API akan memproksikan permintaan secara otomatis ke server FastAPI Anda.",
  },
  {
    q: "Bisakah data dan hasil analisis diekspor?",
    a: "Ya. Setiap hasil analisis dan daftar kluster akun dapat diakses untuk kebutuhan riset, laporan investigasi jurnalistik, atau verifikasi fakta.",
  },
];

export default function FAQ() {
  return (
    <section
      id="faq"
      className="border-t border-[var(--border)] bg-white dark:bg-[var(--card)] py-16 md:py-24 transition-colors duration-200"
    >
      <div className="mx-auto max-w-screen-lg px-4 md:px-6">
        <motion.div
          initial={false}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-40px" }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="text-center max-w-2xl mx-auto mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight text-[var(--foreground)] mt-1.5">
            FAQ
          </h2>
          <p className="mt-3 text-sm md:text-base text-[var(--muted-foreground)] leading-relaxed">
            Hal yang sering ditanyakan mengenai cara kerja, metodologi 3-pilar, dan batasan analisis
          </p>
        </motion.div>

        <motion.div
          initial={false}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mx-auto max-w-2xl"
        >
          <Accordion.Root
            type="single"
            collapsible
            className="divide-y divide-[var(--border)] rounded-2xl border border-[var(--border)] bg-[var(--background)] px-5 shadow-xs"
          >
            {FAQ_ITEMS.map((item, idx) => (
              <Accordion.Item
                key={item.q}
                value={`faq-${idx}`}
                className="border-b last:border-b-0 border-[var(--border)]"
              >
                <Accordion.Header>
                  <Accordion.Trigger className="group flex w-full items-center justify-between gap-4 py-5 text-left text-sm md:text-base font-semibold text-[var(--foreground)] hover:text-[var(--primary)] transition-colors cursor-pointer">
                    <span>{item.q}</span>
                    <ChevronDown
                      size={18}
                      className="shrink-0 text-[var(--muted-foreground)] transition-transform duration-200 group-data-[state=open]:rotate-180 group-data-[state=open]:text-[var(--primary)]"
                    />
                  </Accordion.Trigger>
                </Accordion.Header>
                <Accordion.Content className="overflow-hidden text-sm text-[var(--muted-foreground)] leading-relaxed pb-5 pt-1">
                  {item.a}
                </Accordion.Content>
              </Accordion.Item>
            ))}
          </Accordion.Root>
        </motion.div>
      </div>
    </section>
  );
}
