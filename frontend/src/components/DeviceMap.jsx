import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'

export default function DeviceMap({ devices, onSelect }) {
  const withCoords = devices.filter((d) => d.latitude && d.longitude)
  const center = withCoords.length
    ? [withCoords[0].latitude, withCoords[0].longitude]
    : [28.6139, 77.209] // fallback: New Delhi

  return (
    <MapContainer center={center} zoom={withCoords.length ? 10 : 5} style={{ height: '360px', width: '100%', borderRadius: '12px' }}>
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {withCoords.map((d) => (
        <Marker key={d.id} position={[d.latitude, d.longitude]} eventHandlers={{ click: () => onSelect?.(d) }}>
          <Popup>
            <b>{d.name}</b>
            <br />
            {d.serial_number}
            <br />
            {d.is_active ? 'Active' : 'Inactive'}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
