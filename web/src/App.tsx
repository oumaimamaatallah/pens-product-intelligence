import { useEffect, useState } from "react"
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts"
import {
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  Box,
  Check,
  ExternalLink,
  FileSpreadsheet,
  Grid2X2,
  Info,
  LayoutList,
  Search,
  SlidersHorizontal,
  Star,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Slider } from "@/components/ui/slider"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet"
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import {
  Table,
  TableHeader,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
} from "@/components/ui/table"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Pick } from "@/components/pick"
import { count, percent, useData } from "@/lib/data"

type Product = {
  sku: string
  product_name: string
  category: string
  unit_price_low: number | null
  unit_price_high: number | null
  regular_price: number | null
  minimum_order: number | null
  rating: number | null
  review_count: number | null
  ship_days: number | null
  material: string
  imprint_process: string
  colors: string
  color_count: number
  product_url: string
  image: string
  observed_at: string
  specifications: Record<string, string>
  tiers: { quantity: number; unit_price: number }[]
}
type Catalog = {
  products: Product[]
  count: number
  total: number
  categories: string[]
  groups: { category: string; products: number; median: number; low: number; high: number }[]
  median_price: number | null
  median_minimum: number | null
  average_rating: number | null
  snapshot: string
}
type Scenario = {
  summary: { revenue: number; orders: number; units: number; gross_profit: number; margin: number }
  monthly: { month: string; revenue: number; gross_profit: number }[]
  segments: { customer_segment: string; revenue: number }[]
  channels: string[]
  count: number
  start: string
  end: string
}
type Sources = {
  scrape: {
    observed_at: string
    scope: string
    pages_fetched: { url: string; observed_at: string }[]
    errors: unknown[]
    products: number
  }
  scenario: { orders: number; lines: number; assumptions: string[] }
  coverage: { field: string; percent: number }[]
}
const shades: Record<string, string> = {
  Pens: "#273ed1",
  Drinkware: "#ea5c3d",
  Bags: "#8e9e86",
  Notebooks: "#c3a561",
}
const usd = (value: number | null, digits = 2) =>
  value === null
    ? "Not listed"
    : new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: digits,
      }).format(value)

export default function App() {
  const [tab, setTab] = useState("catalog"),
    [category, setCategory] = useState("all"),
    [query, setQuery] = useState("")
  const [rated, setRated] = useState(false),
    [maxPrice, setMaxPrice] = useState(25),
    [list, setList] = useState(false),
    [catalogPage, setCatalogPage] = useState(0)
  const [product, setProduct] = useState<Product | null>(null),
    [quantity, setQuantity] = useState(50),
    [sort, setSort] = useState("Catalog order")
  const [scenarioCategory, setScenarioCategory] = useState("all"),
    [channel, setChannel] = useState("all"),
    [start, setStart] = useState(""),
    [end, setEnd] = useState("")
  const { data: full } = useData<Catalog>("/api/catalog")
  const params = new URLSearchParams({
    category,
    q: query,
    rated: String(rated),
    max_price: String(maxPrice),
  })
  const { data, error, loading } = useData<Catalog>("/api/catalog?" + params.toString())
  const scenarioParams = new URLSearchParams({
    category: scenarioCategory,
    channel,
    ...(start ? { start } : {}),
    ...(end ? { end } : {}),
  })
  const { data: scenario } = useData<Scenario>("/api/scenario?" + scenarioParams.toString())
  const { data: sources } = useData<Sources>("/api/sources")
  const openProduct = (item: Product) => {
    setProduct(item)
    setQuantity(item.minimum_order || 50)
  }
  const products = [...(data?.products ?? [])].sort((a, b) =>
    sort === "Price: low to high"
      ? (a.unit_price_low ?? Infinity) - (b.unit_price_low ?? Infinity)
      : sort === "Most reviewed"
        ? (b.review_count ?? 0) - (a.review_count ?? 0)
        : 0,
  )
  useEffect(() => setCatalogPage(0), [category, query, rated, maxPrice, sort])
  const pageProducts = products.slice(catalogPage * 12, (catalogPage + 1) * 12)
  const tier = product?.tiers
    .filter((item) => item.quantity <= quantity)
    .sort((a, b) => b.quantity - a.quantity)[0]
  const maxQuantity = Math.max(
    product?.minimum_order || 50,
    ...(product?.tiers.map((item) => item.quantity) ?? [5000]),
  )
  return (
    <TooltipProvider>
      <div className="notebook-shell">
        <header className="notebook-header">
          <a
            href="#"
            className="notebook-logo"
            onClick={(event) => {
              event.preventDefault()
              setTab("catalog")
            }}
          >
            <span className="pn-mark">
              pn<span>.</span>
            </span>
            <span>
              PRODUCT
              <br />
              <b>NOTEBOOK</b>
            </span>
          </a>
          <nav aria-label="Main navigation">
            {[
              { id: "catalog", label: "The catalog" },
              { id: "pricing", label: "Price notes" },
              { id: "scenario", label: "Sales model" },
              { id: "sources", label: "Sources" },
            ].map((item) => (
              <button
                key={item.id}
                className={tab === item.id ? "selected" : ""}
                onClick={() => setTab(item.id)}
              >
                {item.label}
              </button>
            ))}
          </nav>
          <a className="powerbi-link" href="/api/powerbi" download>
            <FileSpreadsheet size={17} />
            <span>Power BI report</span>
            <ArrowUpRight size={15} />
          </a>
        </header>
        <main className="notebook-main">
          <div className="notebook-kicker">
            <span>
              <i />
              PENS.COM / INDEPENDENT CATALOG STUDY
            </span>
            <span>
              US STOREFRONT <i className="slash" /> {data?.snapshot ?? "2026"}
            </span>
          </div>
          <section className="notebook-intro">
            <div>
              <p className="chapter">
                FIELD NOTES /{" "}
                {tab === "catalog"
                  ? "01"
                  : tab === "pricing"
                    ? "02"
                    : tab === "scenario"
                      ? "03"
                      : "04"}
              </p>
              <h1>
                {tab === "catalog" ? (
                  <>
                    Good products.
                    <br />
                    Better questions.
                  </>
                ) : tab === "pricing" ? (
                  <>
                    The price
                    <br />
                    of a first impression.
                  </>
                ) : tab === "scenario" ? (
                  <>
                    If this were
                    <br />a sales desk.
                  </>
                ) : (
                  <>
                    Where the
                    <br />
                    numbers come from.
                  </>
                )}
              </h1>
              <p className="intro-copy">
                {tab === "catalog"
                  ? "An inside look at a public catalog. Compare the details that make one promotional product different from the next."
                  : tab === "pricing"
                    ? "Bulk prices tell a different story. Look at entry points, minimum quantities, and the ratings alongside them."
                    : tab === "scenario"
                      ? "A separate, fictional order book built around these products. Useful for testing a commercial analysis."
                      : "Every catalog fact has a source. Every invented sales record is labeled. Here is the line between the two."}
              </p>
            </div>
            <div className="catalog-tally">
              <span className="tally-number">{String(data?.total ?? 0).padStart(3, "0")}</span>
              <div>
                <strong>products, observed.</strong>
                <p>
                  4 categories
                  <br />
                  One public snapshot.
                </p>
                <span className="tally-lines">||||||||||||||||||||||||</span>
              </div>
            </div>
          </section>
          {(tab === "catalog" || tab === "pricing") && (
            <>
              <div className="category-strip">
                <div className="category-buttons">
                  <button
                    className={category === "all" ? "active" : ""}
                    onClick={() => setCategory("all")}
                  >
                    All products <span>{full?.total ?? 0}</span>
                  </button>
                  {full?.categories.map((name) => (
                    <button
                      key={name}
                      className={category === name ? "active" : ""}
                      onClick={() => setCategory(name)}
                    >
                      <i style={{ background: shades[name] }} />
                      {name}
                      <span>
                        {full.groups.find((group) => group.category === name)?.products ?? 0}
                      </span>
                    </button>
                  ))}
                </div>
                <div className="catalog-summary">
                  <span>
                    Median from-price <b>{usd(data?.median_price ?? null)}</b>
                  </span>
                  <span>
                    Min. order median <b>{data?.median_minimum ?? 0} units</b>
                  </span>
                </div>
              </div>
              <div className="catalog-toolbar">
                <label className="catalog-search">
                  <Search size={16} />
                  <Input
                    aria-label="Search products"
                    placeholder="A product, a material, a SKU..."
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                  />
                </label>
                <div className="catalog-actions">
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm">
                        <SlidersHorizontal size={15} />
                        Refine
                        {rated || maxPrice < 25 ? <span className="filter-count">•</span> : null}
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="refine-dialog">
                      <DialogHeader>
                        <DialogTitle>Find a better fit</DialogTitle>
                        <DialogDescription>
                          Filter the observed catalog. Sales-model filters are separate.
                        </DialogDescription>
                      </DialogHeader>
                      <label className="checkbox-line">
                        <Checkbox
                          checked={rated}
                          onCheckedChange={(value) => setRated(value === true)}
                        />
                        Only products with a public rating
                      </label>
                      <div>
                        <div className="quantity-label">
                          <span>Maximum starting unit price</span>
                          <b>{usd(maxPrice, 0)}</b>
                        </div>
                        <Slider
                          aria-label="Maximum starting price"
                          min={1}
                          max={25}
                          step={1}
                          value={[maxPrice]}
                          onValueChange={(value) => setMaxPrice(value[0])}
                        />
                      </div>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setRated(false)
                          setMaxPrice(25)
                        }}
                      >
                        Clear refinement
                      </Button>
                    </DialogContent>
                  </Dialog>
                  <Pick
                    label="Sort products"
                    value={sort}
                    onChange={setSort}
                    options={["Catalog order", "Price: low to high", "Most reviewed"]}
                  />
                  <div className="view-switch" aria-label="Product layout">
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label="Grid view"
                      className={!list ? "active" : ""}
                      onClick={() => setList(false)}
                    >
                      <Grid2X2 size={16} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label="List view"
                      className={list ? "active" : ""}
                      onClick={() => setList(true)}
                    >
                      <LayoutList size={17} />
                    </Button>
                  </div>
                  <Button variant="ghost" size="icon-sm" asChild>
                    <a
                      href={"/api/export?" + params.toString()}
                      aria-label="Export products"
                      download
                    >
                      <ArrowDownToLine size={16} />
                    </a>
                  </Button>
                </div>
              </div>
            </>
          )}
          {error && (
            <div className="notebook-empty" role="alert">
              {error}
            </div>
          )}
          {!data && loading && <div className="notebook-empty">Opening the notebook...</div>}
          {tab === "catalog" && data && (
            <div
              className={loading ? "catalog-body refreshing" : "catalog-body"}
              aria-busy={loading}
            >
              <div className="results-line">
                <span>
                  <b>{data.count}</b> products in this view
                </span>
                <span>Public prices / USD / quantity tiers vary</span>
              </div>
              {!products.length ? (
                <div className="notebook-empty">
                  <Box size={30} />
                  <h2>Nothing on this shelf.</h2>
                  <p>Try a different category, a shorter search, or clear the price refinement.</p>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setQuery("")
                      setCategory("all")
                      setRated(false)
                      setMaxPrice(25)
                    }}
                  >
                    Reset catalog
                  </Button>
                </div>
              ) : list ? (
                <div className="notebook-table">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {["Product", "Category", "Price range", "Minimum", "Rating", ""].map(
                          (name, index) => (
                            <TableHead key={index}>{name}</TableHead>
                          ),
                        )}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pageProducts.map((item) => (
                        <TableRow
                          key={item.sku}
                          onClick={() => openProduct(item)}
                          className="clickable-row"
                        >
                          <TableCell>
                            <div className="list-product">
                              <img src={item.image} alt="" loading="lazy" />
                              <div>
                                <small>{item.sku}</small>
                                <strong>{item.product_name}</strong>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>{item.category}</TableCell>
                          <TableCell>
                            {usd(item.unit_price_low)} - {usd(item.unit_price_high)}
                          </TableCell>
                          <TableCell>{item.minimum_order ?? "Not listed"}</TableCell>
                          <TableCell>{item.rating ?? "Not listed"}</TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              aria-label={"Inspect " + item.sku}
                              onClick={() => openProduct(item)}
                            >
                              <ArrowUpRight size={16} />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="product-grid">
                  {pageProducts.map((item, index) => (
                    <button
                      className="catalog-product"
                      key={item.sku}
                      onClick={() => openProduct(item)}
                      style={{ animationDelay: Math.min(index, 12) * 25 + "ms" }}
                    >
                      <div className="product-image">
                        <span className="product-sku">{item.sku}</span>
                        <img
                          src={item.image}
                          alt={item.product_name}
                          loading={index < 8 ? "eager" : "lazy"}
                          onError={(event) => {
                            event.currentTarget.style.opacity = "0"
                          }}
                        />
                        <span className="inspect-arrow">
                          <ArrowUpRight size={18} />
                        </span>
                        <span className="product-type" style={{ color: shades[item.category] }}>
                          {item.category}
                        </span>
                      </div>
                      <div className="product-copy">
                        <h2>{item.product_name}</h2>
                        <p>
                          {item.material || "Material not listed"} <span>/</span>{" "}
                          {item.minimum_order ?? "?"} unit minimum
                        </p>
                        <div className="product-price">
                          <div>
                            <small>FROM</small>
                            <strong>{usd(item.unit_price_low)}</strong>
                          </div>
                          <span>
                            {item.rating !== null ? (
                              <>
                                <Star size={11} fill="currentColor" />
                                {item.rating.toFixed(1)}{" "}
                                <small>({count(item.review_count ?? 0)})</small>
                              </>
                            ) : (
                              "No ratings listed"
                            )}
                          </span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
              <div className="catalog-pagination">
                <span>
                  {data.count ? catalogPage * 12 + 1 : 0} -{" "}
                  {Math.min((catalogPage + 1) * 12, data.count)} of {data.count} products
                </span>
                <div>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={catalogPage === 0}
                    onClick={() => setCatalogPage((value) => value - 1)}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={(catalogPage + 1) * 12 >= data.count}
                    onClick={() => setCatalogPage((value) => value + 1)}
                  >
                    Next <ArrowRight size={13} />
                  </Button>
                </div>
              </div>
            </div>
          )}
          {tab === "pricing" && data && (
            <div className="pricing-layout">
              <section className="price-paper">
                <div className="paper-label">01 / PRICE LADDER</div>
                <h2>Different jobs. Different starting points.</h2>
                <p>Observed ranges, with the category median marked in blue.</p>
                <div className="price-ladders">
                  {data.groups.map((group) => (
                    <div className="price-ladder" key={group.category}>
                      <div>
                        <strong>{group.category}</strong>
                        <span>{group.products} products</span>
                      </div>
                      <div className="ladder-track">
                        <span
                          style={{
                            left: Math.min((group.low / 25) * 100, 95) + "%",
                            width:
                              Math.max(
                                2,
                                Math.min(
                                  ((group.high - group.low) / 25) * 100,
                                  100 - (group.low / 25) * 100,
                                ),
                              ) + "%",
                            background: shades[group.category],
                          }}
                        />
                        <i style={{ left: Math.min((group.median / 25) * 100, 98) + "%" }} />
                      </div>
                      <div className="ladder-values">
                        <span>{usd(group.low)}</span>
                        <strong>Median {usd(group.median)}</strong>
                        <span>{usd(group.high)}</span>
                      </div>
                    </div>
                  ))}
                </div>
                <p className="paper-footnote">
                  Lowest advertised unit prices usually require larger quantities. They are not a
                  quote for the minimum order.
                </p>
              </section>
              <section className="price-paper">
                <div className="paper-label">02 / PRICE × PERCEPTION</div>
                <h2>Is a higher price rated better?</h2>
                <p>Each dot is a product. Size represents the public order minimum.</p>
                <div className="rating-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart margin={{ left: 0, right: 18, top: 20, bottom: 20 }}>
                      <CartesianGrid stroke="#eceef3" strokeDasharray="3 4" />
                      <XAxis
                        type="number"
                        dataKey="unit_price_low"
                        name="From-price"
                        unit="$"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 10 }}
                      />
                      <YAxis
                        type="number"
                        dataKey="rating"
                        name="Public rating"
                        domain={[0, 5]}
                        axisLine={false}
                        tickLine={false}
                        width={25}
                        tick={{ fontSize: 10 }}
                      />
                      <ZAxis dataKey="minimum_order" range={[30, 260]} />
                      <Tooltip
                        cursor={{ stroke: "#c5cbdc" }}
                        content={({ active, payload }) =>
                          active && payload?.length ? (
                            <div className="notebook-chart-tooltip">
                              <strong>{payload[0].payload.product_name}</strong>
                              <p>
                                {usd(payload[0].payload.unit_price_low)} /{" "}
                                {payload[0].payload.rating} stars
                              </p>
                            </div>
                          ) : null
                        }
                      />
                      {data.categories.map((name) => (
                        <Scatter
                          key={name}
                          name={name}
                          data={data.products.filter(
                            (item) => item.category === name && item.rating !== null,
                          )}
                          fill={shades[name]}
                          fillOpacity={0.65}
                        />
                      ))}
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>
                <div className="category-legend">
                  {data.categories.map((name) => (
                    <span key={name}>
                      <i style={{ background: shades[name] }} />
                      {name}
                    </span>
                  ))}
                </div>
                <p className="paper-footnote">
                  Ratings are unweighted product averages. Review counts are not sales volumes.
                </p>
              </section>
            </div>
          )}
          {tab === "scenario" && scenario && (
            <>
              <div className="simulation-banner">
                <Info size={18} />
                <p>
                  <b>A scenario, not company sales.</b> Orders, customer groups, channels and costs
                  are fictional. Product prices anchor the assumptions.
                </p>
                <Badge variant="outline">SIMULATED</Badge>
              </div>
              <div className="scenario-controls">
                <Pick
                  label="Scenario category"
                  value={scenarioCategory}
                  onChange={setScenarioCategory}
                  options={full?.categories ?? []}
                  all="All products"
                />
                <Pick
                  label="Sales channel"
                  value={channel}
                  onChange={setChannel}
                  options={scenario.channels}
                  all="All channels"
                />
                <label>
                  <span className="field-label">From</span>
                  <Input
                    aria-label="Scenario start"
                    type="date"
                    value={start || scenario.start}
                    onChange={(event) => setStart(event.target.value)}
                  />
                </label>
                <label>
                  <span className="field-label">To</span>
                  <Input
                    aria-label="Scenario end"
                    type="date"
                    value={end || scenario.end}
                    onChange={(event) => setEnd(event.target.value)}
                  />
                </label>
              </div>
              <section className="scenario-stat-strip">
                <div>
                  <span>SIMULATED NET SALES</span>
                  <strong>{usd(scenario.summary.revenue, 0)}</strong>
                </div>
                <div>
                  <span>DELIVERED ORDERS</span>
                  <strong>{count(scenario.summary.orders)}</strong>
                </div>
                <div>
                  <span>UNITS DELIVERED</span>
                  <strong>{count(scenario.summary.units)}</strong>
                </div>
                <div>
                  <span>ASSUMED GROSS MARGIN</span>
                  <strong>{percent(scenario.summary.margin)}</strong>
                </div>
              </section>
              <div className="scenario-charts">
                <section className="price-paper">
                  <div className="paper-label">THE ORDER BOOK / 2025</div>
                  <h2>A year in the sales model</h2>
                  <div className="scenario-trend">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={scenario.monthly}>
                        <CartesianGrid vertical={false} stroke="#e9edf2" strokeDasharray="3 4" />
                        <XAxis
                          dataKey="month"
                          tickFormatter={(value) =>
                            new Date(value).toLocaleDateString("en-GB", { month: "short" })
                          }
                          axisLine={false}
                          tickLine={false}
                          tick={{ fontSize: 10 }}
                        />
                        <YAxis
                          width={47}
                          tickFormatter={(value) => "$" + Math.round(Number(value) / 1000) + "k"}
                          tick={{ fontSize: 10 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip
                          formatter={(value, name) => [
                            usd(Number(value), 0),
                            name === "revenue" ? "Simulated sales" : "Assumed profit",
                          ]}
                          labelFormatter={(value) =>
                            new Date(String(value)).toLocaleDateString("en-GB", { month: "long" })
                          }
                        />
                        <Area
                          dataKey="revenue"
                          type="monotone"
                          stroke="#293ed0"
                          fill="#e6eaff"
                          strokeWidth={2.5}
                        />
                        <Area
                          dataKey="gross_profit"
                          type="monotone"
                          stroke="#ea5c3d"
                          fill="transparent"
                          strokeWidth={2}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="category-legend">
                    <span>
                      <i style={{ background: "#293ed0" }} />
                      Simulated sales
                    </span>
                    <span>
                      <i style={{ background: "#ea5c3d" }} />
                      Assumed profit
                    </span>
                  </div>
                </section>
                <section className="price-paper segment-paper">
                  <div className="paper-label">WHO IS BUYING / FICTIONAL</div>
                  <h2>Customers in the scenario</h2>
                  {scenario.segments
                    .sort((a, b) => b.revenue - a.revenue)
                    .map((segment) => (
                      <div className="buyer-row" key={segment.customer_segment}>
                        <span>{segment.customer_segment}</span>
                        <b>{usd(segment.revenue, 0)}</b>
                        <div>
                          <i
                            style={{
                              width: percent(segment.revenue / (scenario.summary.revenue || 1)),
                            }}
                          />
                        </div>
                      </div>
                    ))}
                </section>
              </div>
            </>
          )}
          {tab === "sources" && sources && (
            <div className="sources-layout">
              <section className="price-paper">
                <div className="paper-label">THE PUBLIC SIDE</div>
                <h2>A snapshot you can trace.</h2>
                <p>{sources.scrape.scope}.</p>
                <div className="source-numbers">
                  <div>
                    <strong>{sources.scrape.products}</strong>
                    <span>unique products</span>
                  </div>
                  <div>
                    <strong>{sources.scrape.pages_fetched.length}</strong>
                    <span>pages read</span>
                  </div>
                  <div>
                    <strong>{sources.scrape.errors.length}</strong>
                    <span>capture errors</span>
                  </div>
                </div>
                <p>
                  Product names, price ranges, ratings, order minimums and specifications come from
                  public Pens.com pages. Unknown facts stay blank.
                </p>
                <div className="coverage-list">
                  {sources.coverage.map((item) => (
                    <div key={item.field}>
                      <span>{item.field.replaceAll("_", " ")}</span>
                      <div>
                        <i style={{ width: item.percent + "%" }} />
                      </div>
                      <b>{Math.round(item.percent)}%</b>
                    </div>
                  ))}
                </div>
                <a
                  href="https://www.pens.com/us/"
                  target="_blank"
                  rel="noreferrer"
                  className="source-link"
                >
                  Visit the source storefront <ExternalLink size={14} />
                </a>
              </section>
              <section className="price-paper">
                <div className="paper-label">THE ASSUMED SIDE</div>
                <h2>Room to test an idea.</h2>
                <p>
                  {count(sources.scenario.orders)} fictional orders and{" "}
                  {count(sources.scenario.lines)} item rows. The company did not provide these
                  transactions.
                </p>
                <ul className="assumption-list">
                  {sources.scenario.assumptions.map((item) => (
                    <li key={item}>
                      <Check size={14} />
                      {item}
                    </li>
                  ))}
                </ul>
                <div className="powerbi-download">
                  <FileSpreadsheet size={28} />
                  <h3>Take it into Power BI.</h3>
                  <p>
                    The native project includes embedded snapshots, DAX measures and two report
                    pages. Open the PBIP file, then Refresh.
                  </p>
                  <Button asChild>
                    <a href="/api/powerbi" download>
                      Download Power BI project <ArrowDownToLine size={15} />
                    </a>
                  </Button>
                </div>
              </section>
            </div>
          )}
          <footer className="notebook-footer">
            <span>Independent follow-up to Oumaima Maatallah's Pens.com internship.</span>
            <span>Public catalog facts. Separate simulated sales.</span>
          </footer>
        </main>
        <Sheet
          open={!!product}
          onOpenChange={(open) => {
            if (!open) setProduct(null)
          }}
        >
          <SheetContent className="product-sheet">
            {product && (
              <>
                <SheetHeader className="product-sheet-header">
                  <div className="sheet-sku">
                    {product.sku} / {product.category}
                  </div>
                  <SheetTitle>{product.product_name}</SheetTitle>
                  <SheetDescription>
                    {product.material || "Material not listed"} /{" "}
                    {product.imprint_process || "Print method not listed"}
                  </SheetDescription>
                </SheetHeader>
                <div className="product-sheet-scroll">
                  <div className="sheet-product-image">
                    <img src={product.image} alt={product.product_name} />
                  </div>
                  <div className="sheet-rating">
                    {product.rating !== null ? (
                      <>
                        <Star size={13} fill="currentColor" />
                        {product.rating}{" "}
                        <span>from {count(product.review_count ?? 0)} reviews</span>
                      </>
                    ) : (
                      "No public ratings listed"
                    )}
                    <span className="sheet-shipping">
                      {product.ship_days
                        ? product.ship_days + " business-day production estimate"
                        : "Timing not listed"}
                    </span>
                  </div>
                  <section className="quantity-inspector">
                    <div className="paper-label">QUANTITY / PRICE INSPECTOR</div>
                    <div className="quantity-label">
                      <span>Order quantity</span>
                      <strong>{count(quantity)} units</strong>
                    </div>
                    <Slider
                      aria-label="Order quantity"
                      min={product.minimum_order || 1}
                      max={maxQuantity}
                      step={product.minimum_order || 1}
                      value={[quantity]}
                      onValueChange={(value) => setQuantity(value[0])}
                    />
                    {tier ? (
                      <div className="quote-result">
                        <div>
                          <small>OBSERVED UNIT PRICE</small>
                          <strong>{usd(tier.unit_price)}</strong>
                        </div>
                        <div>
                          <small>ITEM SUBTOTAL</small>
                          <strong>{usd(tier.unit_price * quantity)}</strong>
                        </div>
                      </div>
                    ) : (
                      <p className="paper-footnote">
                        No applicable price tier was captured for this quantity.
                      </p>
                    )}
                    <p className="paper-footnote">
                      Public tier from this snapshot. Excludes setup, tax and shipping. Check the
                      source for current pricing and options.
                    </p>
                  </section>
                  <h3 className="specs-title">Product details</h3>
                  <dl className="product-specs">
                    {Object.entries(product.specifications).map(([key, value]) => (
                      <div key={key}>
                        <dt>{key}</dt>
                        <dd>{value}</dd>
                      </div>
                    ))}
                  </dl>
                  <Button asChild className="source-button" variant="outline">
                    <a href={product.product_url} target="_blank" rel="noreferrer">
                      Open this product on Pens.com <ArrowUpRight size={16} />
                    </a>
                  </Button>
                </div>
              </>
            )}
          </SheetContent>
        </Sheet>
      </div>
    </TooltipProvider>
  )
}
