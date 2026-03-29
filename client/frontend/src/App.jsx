import React, { useEffect, useState } from 'react'

export default function App() {
    const [message, setMessage] = useState('Loading...')
    useEffect(() => {
        const api = import.meta.env.DEV
            ? '/api'
            : (import.meta.env.VITE_API_URL || '')

        fetch(api + '/')
            .then(r => r.text())
            .then(t => setMessage(t))
            .catch(() => setMessage('Could not reach backend'))
    }, [])

    return (
        <div style={{ fontFamily: 'system-ui,Segoe UI,Roboto', padding: 20 }}>
            <h1>Guardian Network</h1>
            <p>{message}</p>
        </div>
    )
}
