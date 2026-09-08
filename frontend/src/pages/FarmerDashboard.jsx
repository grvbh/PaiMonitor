import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listDevices, getSummary, logout } from '../api/client.js'
import DeviceMap from '../components/DeviceMap.jsx'
import DensityChart from '../components/DensityChart.jsx'

export default function FarmerDashboard() {
  const [devices, setDevices] = useState([])
  const [selected, setSelected] = useState(null)
  const [summary, setSummary] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    listDevices().then((d) => {
      setDevices(d)
      if (d.length) setSelected(d[0])
    })
  }, [])

  useEffect(() => {
    if (selected) getSummary(selected.id).then(setSummary)
  }, [selected])

  return (
    <div className="dashboard">
      <header className="topbar">
        <h1>My Fields — PaiMonitor</h1>
        <button
          className="link"
          onClick={() => {
            logout()
            navigate('/login')
          }}
        >
          Log out
        </button>
      </header>

      <div className="grid">
        <div className="card">
          <h3>My Devices</h3>
          <ul className="device-list">
            {devices.map((d) => (
              <li
                key={d.id}
                className={selected?.id === d.id ? 'selected' : ''}
                onClick={() => setSelected(d)}
              >
                <span className={`dot ${d.is_active ? 'green' : 'gray'}`} />
                <div>
                  <div className="device-name">{d.name}</div>
                  <div className="muted small">{d.serial_number} • {d.crop}</div>
                </div>
              </li>
            ))}
            {devices.length === 0 && <p className="muted">No devices registered yet.</p>}
          </ul>
        </div>

        <div className="card">
          <h3>Field Map</h3>
          <DeviceMap devices={devices} onSelect={setSelected} />
        </div>
      </div>

      {selected && (
        <>
          <div className="grid">
            <div className="card stat-card">
              <span className="stat-label">Total Detections</span>
              <span className="stat-value">{summary?.total_detections ?? '—'}</span>
              <span className="muted small">{selected.name}</span>
            </div>
            <div className="card stat-card">
              <span className="stat-label">Top Pest</span>
              <span className="stat-value">{summary?.top_species?.[0]?.species ?? '—'}</span>
              <span className="muted small">
                {summary?.top_species?.[0]?.count ?? 0} counted
              </span>
            </div>
          </div>

          <DensityChart deviceId={selected.id} />
        </>
      )}
    </div>
  )
}
