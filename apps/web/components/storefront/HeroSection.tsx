"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

const banners = [
  { src: "/banner.png", alt: "Ưu đãi Tết và khuyến mãi SmartGrocery" },
  { src: "/banner2.png", alt: "Voucher ưu đãi mua sắm SmartGrocery" },
  { src: "/banner3.png", alt: "Ưu đãi 12.12 cho thực phẩm tươi sống và rau củ" },
  { src: "/banner4.png", alt: "SmartGrocery - mua sắm tươi ngon mỗi ngày" },
];

const sideBanners = [
  banners[3],
  { src: "/banner2.png", alt: "Voucher ưu đãi mua sắm SmartGrocery" },
];

const shortcuts = [
  { href: "/products", icon: "🛍️", label: "Khám phá sản phẩm" },
  { href: "/cart", icon: "🛒", label: "Giỏ hàng của bạn" },
  { href: "/orders", icon: "📦", label: "Theo dõi đơn hàng" },
  { href: "/login", icon: "👤", label: "Tài khoản của tôi" },
];

export default function HeroSection() {
  const [active, setActive] = useState(0);
  const [popupOpen, setPopupOpen] = useState(true);

  useEffect(() => {
    const timer = window.setInterval(
      () => setActive((previous) => (previous + 1) % banners.length),
      4500,
    );
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!popupOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setPopupOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [popupOpen]);

  return (
    <>
      <section className="bg-[#f5f5f5] py-5 md:py-7" aria-label="Khuyến mãi">
        <div className="sg-container">
          <div className="grid gap-2 lg:grid-cols-[2fr_0.95fr]">
            <div
              className="relative overflow-hidden rounded-lg bg-[#0754bd] shadow-sm"
              aria-roledescription="carousel"
              aria-label="Banner khuyến mãi"
            >
              <div
                className="flex aspect-[16/9] transition-transform duration-500 ease-in-out"
                style={{ transform: `translateX(-${active * 100}%)` }}
              >
                {banners.map((banner, index) => (
                  <div
                    key={banner.src}
                    className="relative min-w-full"
                    aria-hidden={index !== active}
                  >
                    <Image
                      src={banner.src}
                      alt={banner.alt}
                      fill
                      priority={index === 0}
                      sizes="(max-width: 1024px) 100vw, 850px"
                      className="object-contain"
                    />
                  </div>
                ))}
              </div>
              <button
                type="button"
                onClick={() =>
                  setActive((previous) => (previous - 1 + banners.length) % banners.length)
                }
                aria-label="Banner trước"
                className="absolute left-3 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-black/35 text-2xl text-white transition hover:bg-black/60"
              >
                ‹
              </button>
              <button
                type="button"
                onClick={() => setActive((previous) => (previous + 1) % banners.length)}
                aria-label="Banner tiếp theo"
                className="absolute right-3 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-black/35 text-2xl text-white transition hover:bg-black/60"
              >
                ›
              </button>
              <div className="absolute bottom-3 left-1/2 flex -translate-x-1/2 gap-2 rounded-full bg-black/30 px-3 py-2">
                {banners.map((banner, index) => (
                  <button
                    key={banner.src}
                    type="button"
                    onClick={() => setActive(index)}
                    aria-label={`Chọn banner ${index + 1}`}
                    aria-current={active === index ? "true" : undefined}
                    className={`h-2 w-2 rounded-full transition ${
                      active === index ? "bg-white" : "bg-white/50"
                    }`}
                  />
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 lg:grid-cols-1">
              {sideBanners.map((banner) => (
                <Link
                  key={banner.src}
                  href="/products"
                  aria-label={`${banner.alt} - xem sản phẩm`}
                  className="relative aspect-[1.65/1] overflow-hidden rounded-lg bg-[#0754bd] shadow-sm transition hover:brightness-105 lg:aspect-[2.4/1]"
                >
                  <Image
                    src={banner.src}
                    alt={banner.alt}
                    fill
                    sizes="(max-width: 1024px) 50vw, 400px"
                    className="object-cover"
                  />
                </Link>
              ))}
            </div>
          </div>

          <nav
            aria-label="Lối tắt mua sắm"
            className="mt-4 grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-4"
          >
            {shortcuts.map((shortcut) => (
              <Link
                key={shortcut.href}
                href={shortcut.href}
                className="flex min-h-24 flex-col items-center justify-center gap-2 bg-white px-2 py-4 text-center text-sm font-medium text-foreground transition hover:text-primary"
              >
                <span className="flex h-11 w-11 items-center justify-center rounded-xl border border-border bg-white text-xl">
                  {shortcut.icon}
                </span>
                {shortcut.label}
              </Link>
            ))}
          </nav>
        </div>
      </section>

      {popupOpen && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Ưu đãi SmartGrocery"
        >
          <div className="relative w-[92vw] max-w-[520px] overflow-hidden rounded-2xl bg-white p-3 shadow-2xl">
            <button
              type="button"
              onClick={() => setPopupOpen(false)}
              aria-label="Đóng quảng cáo"
              className="absolute right-5 top-5 z-10 flex h-10 w-10 items-center justify-center rounded-full bg-black/70 text-2xl text-white hover:bg-black"
            >
              ×
            </button>
            <Image
              src="/bannerpopup.png"
              alt="Đại sứ thương hiệu SmartGrocery và chương trình 12.12 siêu sale"
              width={1254}
              height={1254}
              priority
              sizes="(max-width: 520px) 92vw, 520px"
              className="max-h-[70vh] w-full rounded-lg object-contain"
            />
            <Link
              href="/products"
              onClick={() => setPopupOpen(false)}
              className="mt-3 block w-full rounded-xl bg-primary px-5 py-3 text-center font-semibold text-white hover:bg-primary-dark"
            >
              Mua sắm ngay
            </Link>
          </div>
        </div>
      )}
    </>
  );
}
