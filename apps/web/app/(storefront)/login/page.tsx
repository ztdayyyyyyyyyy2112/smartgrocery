export default function LoginPage() {
  return (
    <section className="sg-container py-16 md:py-20">
      <div className="mx-auto max-w-lg rounded-2xl border border-border bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-dark">
          Account
        </p>
        <h1 className="mt-4 text-4xl font-bold tracking-tight text-foreground">Welcome back</h1>
        <p className="mt-3 text-muted">
          Login flows are intentionally left as placeholders for SG-07. No real
          authentication logic is implemented in this frontend shell.
        </p>

        <form className="mt-8 space-y-5">
          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-medium text-foreground">
              Email address
            </label>
            <input
              id="email"
              type="email"
              placeholder="merchant@smartgrocery.vn"
              className="w-full rounded-xl border border-border bg-background px-4 py-3 text-foreground outline-none transition focus:border-primary focus:ring-2 focus:ring-primary-light"
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-2 block text-sm font-medium text-foreground">
              Password
            </label>
            <input
              id="password"
              type="password"
              placeholder="••••••••"
              className="w-full rounded-xl border border-border bg-background px-4 py-3 text-foreground outline-none transition focus:border-primary focus:ring-2 focus:ring-primary-light"
            />
          </div>

          <button
            type="button"
            className="w-full rounded-xl bg-primary px-4 py-3 font-semibold text-white transition hover:bg-primary-dark focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-primary-dark"
          >
            Demo login
          </button>
        </form>
      </div>
    </section>
  );
}
