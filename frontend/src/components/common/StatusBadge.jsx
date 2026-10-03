import { CheckCircle2, Loader2, AlertCircle } from 'lucide-react'

const CONFIG = {
  ready: {
    icon: CheckCircle2,
    label: 'Ready',
    className: 'text-[var(--color-success)] bg-[var(--color-success-soft)]',
  },
  processing: {
    icon: Loader2,
    label: 'Processing',
    className: 'text-[var(--color-warning)] bg-[var(--color-warning-soft)]',
    spin: true,
  },
  failed: {
    icon: AlertCircle,
    label: 'Failed',
    className: 'text-[var(--color-danger)] bg-[var(--color-danger-soft)]',
  },
}

export default function StatusBadge({ status }) {
  const config = CONFIG[status] ?? CONFIG.processing
  const Icon = config.icon
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${config.className}`}
    >
      <Icon size={11} className={config.spin ? 'animate-spin' : ''} />
      {config.label}
    </span>
  )
}
