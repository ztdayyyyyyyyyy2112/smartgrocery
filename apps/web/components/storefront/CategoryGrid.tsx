import Image from "next/image";
import { groceryCategories } from "../../lib/mock-data";

const categoryLabels: Record<string, { name: string; description: string }> = {
  Vegetables: { name: "Rau củ", description: "Tươi ngon mỗi ngày" },
  Fruits: { name: "Trái cây", description: "Theo mùa chọn lọc" },
  "Dairy & Eggs": { name: "Sữa & trứng", description: "Thiết yếu hàng ngày" },
  "Meat & Seafood": { name: "Thịt & hải sản", description: "Tươi sạch chất lượng" },
  Beverages: { name: "Đồ uống", description: "Giải khát tiện lợi" },
  "Pantry Essentials": { name: "Thực phẩm khô", description: "Đủ đầy gian bếp" },
};

export default function CategoryGrid() {
  return (
    <section className="bg-[#f5f5f5] pb-7 md:pb-10">
      <div className="sg-container">
        <div className="overflow-hidden border border-border bg-white">
          <h2 className="border-b border-border px-5 py-4 text-base font-semibold uppercase tracking-wide text-muted">
            Danh mục sản phẩm
          </h2>
          <div className="grid grid-cols-2 gap-px bg-border sm:grid-cols-3 lg:grid-cols-6">
            {groceryCategories.map((category, index) => (
              <article
                key={category.name}
                className="flex min-w-0 flex-col items-center bg-white px-3 py-5 text-center transition-colors hover:bg-primary-light/30"
              >
                <div className="relative h-16 w-16 overflow-hidden rounded-full bg-[#f7f7f7] ring-1 ring-border sm:h-20 sm:w-20">
                  <Image
                    src={category.imageSrc}
                    alt={categoryLabels[category.name]?.name ?? category.name}
                    fill
                    loading={index === 0 ? "eager" : "lazy"}
                    sizes="(max-width: 640px) 64px, 80px"
                    className="object-cover"
                  />
                </div>
                <h3 className="mt-3 text-sm font-medium text-foreground">
                  {categoryLabels[category.name]?.name ?? category.name}
                </h3>
                <p className="mt-1 text-xs text-muted">
                  {categoryLabels[category.name]?.description ?? category.description}
                </p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
