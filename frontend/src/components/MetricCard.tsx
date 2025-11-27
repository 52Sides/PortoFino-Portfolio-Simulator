interface MetricCardProps {
  label: string;
  value: string | number;
}

export default function MetricCard({ label, value }: MetricCardProps) {
  return (
    <div className="bg-[var(--surface)] text-[var(--text)] rounded-xl shadow-md p-6 flex flex-col items-center justify-center transition-colors duration-300 hover:shadow-lg">
      <p className="text-sm text-[var(--text-muted)] mb-2">{label}</p>
      <p className="text-xl font-semibold">{value}</p>
    </div>
  );
}
