// Demo/mock data for SG-07 storefront prototype. Replace with live API data later.

export type Product = {
  id: string;
  name: string;
  category: string;
  price: number;
  unit: string;
  stock: "In stock" | "Low stock";
  imageLabel: string;
  description: string;
};

export type Category = {
  name: string;
  icon: string;
  description: string;
};

export const groceryCategories: Category[] = [
  { name: "Vegetables", icon: "🥬", description: "Fresh picks" },
  { name: "Fruits", icon: "🍋", description: "Seasonal favorites" },
  { name: "Dairy & Eggs", icon: "🥛", description: "Daily essentials" },
  { name: "Meat & Seafood", icon: "🥩", description: "Protein-rich" },
  { name: "Beverages", icon: "🥤", description: "Refreshing" },
  { name: "Pantry Essentials", icon: "🥖", description: "Home staples" },
];

export const featuredProducts: Product[] = [
  {
    id: "tomatoes",
    name: "Fresh Tomatoes",
    category: "Vegetables",
    price: 42000,
    unit: "1kg",
    stock: "In stock",
    imageLabel: "🍅",
    description: "Farm-picked and ready for salads, soups, and sauces.",
  },
  {
    id: "carrots",
    name: "Sweet Carrots",
    category: "Vegetables",
    price: 28000,
    unit: "1kg",
    stock: "In stock",
    imageLabel: "🥕",
    description: "Crisp and naturally sweet for healthy daily meals.",
  },
  {
    id: "bananas",
    name: "Bananas",
    category: "Fruits",
    price: 26000,
    unit: "1 bunch",
    stock: "In stock",
    imageLabel: "🍌",
    description: "Naturally sweet and ready for breakfast, smoothies, and snacks.",
  },
  {
    id: "milk",
    name: "Fresh Milk",
    category: "Dairy & Eggs",
    price: 36000,
    unit: "1L",
    stock: "Low stock",
    imageLabel: "🥛",
    description: "High-quality dairy milk for coffee, cereals, and family meals.",
  },
  {
    id: "eggs",
    name: "Free-Range Eggs",
    category: "Dairy & Eggs",
    price: 48000,
    unit: "10 eggs",
    stock: "In stock",
    imageLabel: "🥚",
    description: "Protein-packed eggs for breakfast, baking, and easy cooking.",
  },
  {
    id: "rice",
    name: "Premium Rice",
    category: "Pantry Essentials",
    price: 65000,
    unit: "5kg",
    stock: "In stock",
    imageLabel: "🍚",
    description: "Long-grain staple rice selected for everyday family meals.",
  },
];
