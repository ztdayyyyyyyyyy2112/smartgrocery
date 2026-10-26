export default function HeroSection() {
  return (
    <section className="bg-background py-5 md:py-7">
      <div className="sg-container">
        <div
          aria-label="Advertising banner area"
          className="flex min-h-40 items-center justify-center rounded-xl border border-dashed border-primary/40 bg-primary-light px-6 py-8 text-center md:min-h-52"
        >
          <div>
            <p className="text-sm font-semibold text-primary-dark md:text-base">
              Advertising banner space
            </p>
            <p className="mt-1 text-sm text-muted">
              Reserved for brand and store campaigns
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
