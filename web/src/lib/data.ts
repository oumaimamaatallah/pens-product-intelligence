import { useEffect, useState } from "react"

export function useData<T>(url: string) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError("")
    fetch(url, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok)
          throw new Error("The data could not be loaded. Check that the local server is running.")
        return response.json()
      })
      .then((value) => {
        setData(value)
        setLoading(false)
      })
      .catch((error) => {
        if (error.name !== "AbortError") {
          setError(error.message)
          setLoading(false)
        }
      })
    return () => controller.abort()
  }, [url])
  return { data, error, loading }
}

export function money(value: number, currency = "EUR", digits = 0) {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency,
    maximumFractionDigits: digits,
  }).format(value)
}
export function count(value: number) {
  return new Intl.NumberFormat("en-GB").format(value)
}
export function percent(value: number) {
  return new Intl.NumberFormat("en-GB", { style: "percent", maximumFractionDigits: 1 }).format(
    value,
  )
}
export function month(value: string) {
  return new Date(value).toLocaleDateString("en-GB", { month: "short" })
}
export function downloadCsv(rows: Record<string, unknown>[], name: string) {
  if (!rows.length) return
  const columns = Object.keys(rows[0])
  const quote = (value: unknown) => '"' + String(value ?? "").replaceAll('"', '""') + '"'
  const content = [
    columns.map(quote).join(","),
    ...rows.map((row) => columns.map((column) => quote(row[column])).join(",")),
  ].join("\n")
  const url = URL.createObjectURL(new Blob([content], { type: "text/csv;charset=utf-8" }))
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = name
  anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
