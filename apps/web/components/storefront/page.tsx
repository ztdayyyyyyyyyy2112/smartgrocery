export default function HomePage() {
  return (
    <main className="min-h-screen py-16">
      <div className="sg-container">

        {/* Heading */}
        <div className="mb-10">
          <span className="mb-3 inline-block rounded-full bg-primary-light px-4 py-2 text-sm font-semibold text-primary-dark">
            SmartGrocery Platform
          </span>

          <h1 className="text-4xl font-bold tracking-tight md:text-5xl">
            Welcome to SmartGrocery
          </h1>

          <p className="mt-4 max-w-2xl text-lg text-muted">
            An intelligent grocery e-commerce platform
            powered by demand forecasting, inventory
            management and smart replenishment.
          </p>
        </div>

        {/* Cards */}
        <div className="grid gap-6 md:grid-cols-3">

          <div className="sg-card">
            <div className="mb-4 text-3xl">🛒</div>

            <h2 className="mb-2 text-xl font-bold">
              Customer Storefront
            </h2>

            <p className="text-muted">
              Browse products, manage your cart
              and place grocery orders.
            </p>
          </div>

          <div className="sg-card">
            <div className="mb-4 text-3xl">📦</div>

            <h2 className="mb-2 text-xl font-bold">
              Inventory Management
            </h2>

            <p className="text-muted">
              Monitor stock levels, inventory
              batches and supplier operations.
            </p>
          </div>

          <div className="sg-card">
            <div className="mb-4 text-3xl">🤖</div>

            <h2 className="mb-2 text-xl font-bold">
              AI Intelligence
            </h2>

            <p className="text-muted">
              Forecast product demand and generate
              intelligent replenishment recommendations.
            </p>
          </div>

        </div>

        {/* Button */}
        <div className="mt-10">
          <button
            type="button"
            className="sg-button-primary"
          >
            Explore SmartGrocery
          </button>
        </div>

      </div>
    </main>
  );
}