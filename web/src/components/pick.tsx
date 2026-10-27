import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select"
export function Pick({
  label,
  value,
  onChange,
  options,
  all,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  options: string[]
  all?: string
}) {
  return (
    <div className="pick">
      <span className="field-label">{label}</span>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger aria-label={label}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {all && <SelectItem value="all">{all}</SelectItem>}
          {options.map((option) => (
            <SelectItem key={option} value={option}>
              {option}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
