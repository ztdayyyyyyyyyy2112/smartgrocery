"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

const banners = [
  { src: "/banner.png", alt: "Ưu đãi Tết SmartGrocery" },
  { src: "/banner2.png", alt: "Ưu đãi voucher 12.12 SmartGrocery" },
  { src: "/banner3.png", alt: "Ưu đãi hàng tươi sống và rau củ 12.12" },
  { src: "/banner4.png", alt: "Chương trình mua sắm hàng tươi sống và rau củ SmartGrocery" },
];

export default function HeroSection() {
  const [active, setActive] = useState(0);
  const [popupOpen, setPopupOpen] = useState(true);

  useEffect(() => {
    const timer = window.setInterval(() => setActive(previous => (previous + 1) % banners.length), 3000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!popupOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setPopupOpen(false); };
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [popupOpen]);

  return (
    <>
      <section className="bg-background py-5 md:py-7" aria-label="Banner khuyến mãi">
        <div className="sg-container">
          <div className="relative overflow-hidden rounded-xl bg-[#0754bd] shadow-sm" aria-roledescription="carousel">
            <div className="flex transition-transform duration-500 ease-in-out" style={{ transform: `translateX(-${active * 100}%)` }}>
              {banners.map((banner, index) => (
                <div key={banner.src} className="relative aspect-[4/3] min-w-full md:aspect-[3/2]" aria-hidden={index !== active}>
                  <Image src={banner.src} alt={banner.alt} fill priority={index === 0} unoptimized sizes="(max-width: 1280px) 100vw, 1280px" className="object-contain" />
                </div>
              ))}
            </div>
            <button type="button" onClick={() => setActive(previous => (previous - 1 + banners.length) % banners.length)} aria-label="Banner trước" className="absolute left-3 top-1/2 -translate-y-1/2 rounded-full bg-black/45 px-3 py-2 text-xl text-white hover:bg-black/65">‹</button>
            <button type="button" onClick={() => setActive(previous => (previous + 1) % banners.length)} aria-label="Banner tiếp theo" className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-black/45 px-3 py-2 text-xl text-white hover:bg-black/65">›</button>
            <div className="absolute bottom-3 left-1/2 flex -translate-x-1/2 gap-2 rounded-full bg-black/35 px-3 py-2" aria-label="Chọn banner">
              {banners.map((banner, index) => (
                <button key={banner.src} type="button" onClick={() => setActive(index)} aria-label={`Banner ${index + 1}`} aria-current={active === index ? "true" : undefined} className={`h-2.5 w-2.5 rounded-full ${active === index ? "bg-white" : "bg-white/50"}`} />
              ))}
            </div>
          </div>
        </div>
      </section>

      {popupOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4" role="dialog" aria-modal="true" aria-label="Ưu đãi SmartGrocery">
          <div className="relative w-[92vw] max-w-[520px] overflow-hidden rounded-2xl bg-white p-3 shadow-2xl">
            <button type="button" onClick={() => setPopupOpen(false)} aria-label="Đóng quảng cáo" className="absolute right-5 top-5 z-10 flex h-10 w-10 items-center justify-center rounded-full bg-black/70 text-2xl text-white hover:bg-black">×</button>
            <Image src="/bannerpopup.png" alt="Đại sứ thương hiệu SmartGrocery và chương trình 12.12 siêu sale" width={1254} height={1254} priority unoptimized sizes="(max-width: 520px) 92vw, 520px" className="max-h-[70vh] w-full rounded-lg object-contain" />
            <button type="button" onClick={() => setPopupOpen(false)} className="mt-3 w-full rounded-xl bg-primary px-5 py-3 font-semibold text-white hover:bg-primary-dark">Mua sắm ngay</button>
          </div>
        </div>
      )}
    </>
  );
}
