"use client";

import * as Accordion from "@radix-ui/react-accordion";
import { ChevronDown } from "lucide-react";

const FAQ_ITEMS = [
  {
    q: "Apakah skor tinggi membuktikan bahwa akun tersebut pasti buzzer bayaran?",
    a: "Tidak. Buzzer Detector mengukur anomali koordinasi statistik dan pola kemiripan bot. Skor tinggi memerlukan tinjauan konteks oleh manusia untuk membedakan antara astroturfing bayaran dengan gerakan aktivisme organik publik.",
  },
  {
    q: "Bagaimana sistem menangani bahasa gaul, singkatan, dan emoji Indonesia?",
    a: "Pra-pemrosesan teks menggunakan tokenizer yang disesuaikan untuk IndoBERTweet: menormalisasi karakter berulang, mengganti tautan/mention dengan token (@USER, HTTPURL), dan mengubah emoji menjadi deskriptor teks bahasa Indonesia tanpa menghapusnya.",
  },
  {
    q: "Mengapa tagar, URL, dan mention tidak dihapus dari teks analisis?",
    a: "Jaringan buzzer terkoordinasi sering kali menyalin-tempel tumpukan tagar yang identik atau mengarahkan balasan ke akun target yang sama persis. Menghapus elemen ini justru akan menghilangkan sinyal struktural terkuat.",
  },
  {
    q: "Data apa saja yang dikumpulkan oleh sistem ini?",
    a: "Hanya cuitan dan profil publik yang dapat diakses secara terbuka (pengikut, yang diikuti, status, bio). Tidak ada data pribadi rahasia atau pesan langsung (DM) yang disimpan.",
  },
  {
    q: "Apakah frontend ini bisa dihubungkan ke model backend Python khusus?",
    a: "Ya. Cukup atur FASTAPI_BACKEND_URL pada environment variable, dan API akan memproksikan permintaan secara otomatis ke server FastAPI IndoBERTweet/GraphSAGE Anda.",
  },
  {
    q: "Bisakah data dan hasil analisis diekspor?",
    a: "Ya. Setiap hasil analisis dan daftar kluster akun dapat diunduh langsung untuk kebutuhan investigasi atau riset lebih lanjut.",
  },
];

export default function FAQ() {
  return (
    <section id="faq" className="border-t border-[var(--border)] bg-white py-16 md:py-20">
      <div className="mx-auto max-w-screen-lg px-4 md:px-6">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-[var(--foreground)]">
            Pertanyaan Umum
          </h2>
          <p className="mt-3 text-sm md:text-base text-[var(--muted-foreground)] leading-relaxed">
            Hal yang sering ditanyakan mengenai cara kerja dan metodologi deteksi buzzer
          </p>
        </div>

        <Accordion.Root
          type="single"
          collapsible
          className="mx-auto max-w-2xl divide-y divide-[var(--border)] rounded-xl border border-[var(--border)] bg-[var(--background)] px-4"
        >
          {FAQ_ITEMS.map((item, idx) => (
            <Accordion.Item
              key={item.q}
              value={`faq-${idx}`}
              className="border-b last:border-b-0 border-[var(--border)]"
            >
              <Accordion.Header>
                <Accordion.Trigger className="group flex w-full items-center justify-between gap-4 py-4.5 text-left text-sm md:text-base font-semibold text-[var(--foreground)] hover:text-[var(--primary)] transition-colors cursor-pointer">
                  <span>{item.q}</span>
                  <ChevronDown
                    size={18}
                    className="shrink-0 text-[var(--muted-foreground)] transition-transform duration-200 group-data-[state=open]:rotate-180 group-data-[state=open]:text-[var(--primary)]"
                  />
                </Accordion.Trigger>
              </Accordion.Header>
              <Accordion.Content className="overflow-hidden text-sm text-[var(--muted-foreground)] leading-relaxed pb-4 pt-1">
                {item.a}
              </Accordion.Content>
            </Accordion.Item>
          ))}
        </Accordion.Root>
      </div>
    </section>
  );
}
