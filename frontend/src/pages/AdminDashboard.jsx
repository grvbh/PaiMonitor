import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listDevices, logout } from '../api/client.js'
import DeviceMap from '../components/DeviceMap.jsx'
import DensityChart from '../components/DensityChart.jsx'

export default function AdminDashboard() {
  const [devices, setDevices] = useState([])
  const [selected, setSelected] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    listDevices().then(setDevices)
  }, [])

  return (
    <div className="dashboard">
      <header className="topbar">
        <h1>Admin — All Devices</h1>
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
          <h3>All Registered Devices ({devices.length})</h3>
          <table className="device-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Serial</th>
                <th>Status</th>
                <th>Last Seen</th>
              </tr>
            </thead>
            <tbody>
              {devices.map((d) => (
                <tr key={d.id} onClick={() => setSelected(d)} className={selected?.id === d.id ? 'selected' : ''}>
                  <td>{d.name}</td>
                  <td>{d.serial_number}</td>
                  <td>{d.is_active ? 'Active' : 'Inactive'}</td>
                  <td>{d.last_seen_at ? new Date(d.last_seen_at).toLocaleString() : 'Never'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h3>Device Map (All Farms)</h3>
          <DeviceMap devices={devices} onSelect={setSelected} />
        </div>
      </div>

      {selected && <DensityChart deviceId={selected.id} />}
    </div>
  )
}
