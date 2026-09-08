import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { getDensity } from '../api/client.js'

const COLORS = ['#e07a1f', '#2f9e44', '#1971c2', '#c92a2a', '#9c36b5', '#0c8599']

function reshape(points) {
  // Turn [{bucket_start, species, count}] into rows keyed by bucket_start,
  // one column per species, for a multi-line recharts chart.
  const bySpecies = new Set()
  const byBucket = {}

  for (const p of points) {
    bySpecies.add(p.species)
    const key = p.bucket_start
    if (!byBucket[key]) byBucket[key] = { bucket_start: key }
    byBucket[key][p.species] = p.count
  }

  const rows = Object.values(byBucket).sort((a, b) => new Date(a.bucket_start) - new Date(b.bucket_start))
  return { rows, species: Array.from(bySpecies) }
}

export default function DensityChart({ deviceId }) {
  const [granularity, setGranularity] = useState('day')
  const [rows, setRows] = useState([])
  const [species, setSpecies] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!deviceId) return
    setLoading(true)
    getDensity(deviceId, granularity)
      .then((data) => {
        const { rows, species } = reshape(data.points)
        setRows(rows)
        setSpecies(species)
      })
      .finally(() => setLoading(false))
  }, [deviceId, granularity])

  return (
    <div className="card">
      <div className="card-header">
        <h3>Insect Density</h3>
        <div className="toggle-group">
          {['day', 'week', 'month'].map((g) => (
            <button key={g} className={g === granularity ? 'active' : ''} onClick={() => setGranularity(g)}>
              {g === 'day' ? 'Per Day' : g === 'week' ? 'Per Week' : 'Per Month'}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <p className="muted">Loading...</p>
      ) : rows.length === 0 ? (
        <p className="muted">No detections yet for this period.</p>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="bucket_start"
              tickFormatter={(v) => new Date(v).toLocaleDateString()}
              fontSize={12}
            />
            <YAxis fontSize={12} allowDecimals={false} />
            <Tooltip labelFormatter={(v) => new Date(v).toLocaleString()} />
            <Legend />
            {species.map((s, i) => (
              <Line key={s} type="monotone" dataKey={s} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
