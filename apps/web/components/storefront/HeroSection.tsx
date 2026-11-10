import Image from "next/image";

export default function HeroSection() {
  return (
    <section className="bg-background py-5 md:py-7">
      <div className="sg-container">
        <Image
          src="/banner.png?v=20261110"
          alt="SGrocery Tet sale promotional banner"
          width={1531}
          height={1027}
          priority
          unoptimized
          sizes="(max-width: 1280px) 100vw, 1280px"
          className="h-auto w-full rounded-xl"
        />
      </div>
    </section>
  );
}
