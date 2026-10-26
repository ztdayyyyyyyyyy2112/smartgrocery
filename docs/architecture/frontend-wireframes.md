# SmartGrocery Frontend Wireframes

## 1. Overview

SmartGrocery provides two main user interfaces:

1. Customer Storefront
2. Merchant Dashboard

The frontend is developed using Next.js,
TypeScript and Tailwind CSS.

## 2. Customer Storefront

### Pages

| Page | Route |
|---|---|
| Homepage | / |
| Products | /products |
| Product Details | /products/[id] |
| Cart | /cart |
| Checkout | /checkout |
| Login | /login |
| Register | /register |
| Orders | /orders |
| Order Details | /orders/[id] |

### Main Components

- Navbar
- HeroSection
- CategoryGrid
- ProductCard
- ProductGrid
- ShoppingCart
- CheckoutForm
- Footer

## 3. Merchant Dashboard

### Pages

| Page | Route |
|---|---|
| Overview | /dashboard |
| Inventory | /dashboard/inventory |
| Orders | /dashboard/orders |
| Forecasting | /dashboard/forecasting |
| Recommendations | /dashboard/recommendations |
| Suppliers | /dashboard/suppliers |
| Procurement | /dashboard/procurement |

### Main Components

- DashboardSidebar
- DashboardHeader
- StatCard
- SalesChart
- InventoryAlert
- ForecastChart
- RecommendationCard
- DataTable

## 4. Navigation

Customer navigation:

Home → Products → Product Details → Cart → Checkout

Merchant navigation:

Dashboard → Inventory → Forecasting →
Recommendations → Procurement

## 5. Responsive Design

The application supports:

- Desktop
- Tablet
- Mobile

Customer pages use responsive grids.

Merchant pages use a collapsible sidebar.

## 6. UI Design Principles

- Clean and modern grocery shopping experience
- Consistent design system
- Reusable components
- Accessible navigation
- Responsive layouts
- Clear inventory and AI visualizations

## 7. Frontend Architecture

Framework: Next.js

Language: TypeScript

Styling: Tailwind CSS

Routing: App Router

API Communication: REST API

## 8. API Integration

Frontend communicates with FastAPI.

Main API domains:

- Authentication
- Products
- Orders
- Inventory
- Suppliers
- Procurement
- Forecasting
- Recommendations

## 9. Acceptance Criteria

- All required pages are documented.
- Navigation structure is defined.
- Main reusable components are identified.
- Customer and Merchant interfaces are separated.
- Responsive design requirements are specified.