import React, { useMemo, useState } from 'react'

const VERDICT_STYLES = {
    ALLOW: 'badge allow',
    BLOCK: 'badge block',
    PAUSED: 'badge paused'
}

function scoreWidth(score) {
    const n = Number.isFinite(score) ? score : 0
    const clamped = Math.max(0, Math.min(100, n))
    return `${clamped}%`
}

export default function App() {
    const apiBase = useMemo(() => {
        return import.meta.env.DEV ? '/api' : (import.meta.env.VITE_API_URL || '')
    }, [])

    const [url, setUrl] = useState('')
    const [context, setContext] = useState('')
    const [deviceId, setDeviceId] = useState('demo-device-1')
    const [userAge, setUserAge] = useState(13)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [decision, setDecision] = useState(null)
    const [overrideNotice, setOverrideNotice] = useState(false)

    async function submitRequest(extra = {}) {
        setLoading(true)
        setError('')

        try {
            const res = await fetch(`${apiBase}/request`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url,
                    request_context: context,
                    device_id: deviceId,
                    user_age: Number(userAge),
                    ...extra
                })
            })

            if (!res.ok) {
                throw new Error(`Request failed with status ${res.status}`)
            }

            const payload = await res.json()
            setDecision(payload)
            return payload
        } catch (err) {
            setError(err.message || 'Could not reach backend')
            return null
        } finally {
            setLoading(false)
        }
    }

    async function onSubmit(e) {
        e.preventDefault()
        setOverrideNotice(false)
        await submitRequest()
    }

    async function requestOverride() {
        const payload = await submitRequest({ override: true })
        if (payload) {
            setOverrideNotice(true)
        }
    }

    const verdict = decision?.verdict || 'PENDING'
    const score = Number(decision?.decision_score ?? decision?.score ?? 0)

    return (
        <main className="page">
            <div className="panel">
                <h1>Guardian Child Access Request</h1>
                <p className="sub">Request access to a site and view the decision response.</p>

                {!decision && (
                    <section>
                        <h2>Request Page</h2>
                        <form onSubmit={onSubmit} className="stack">
                            <label>
                                URL
                                <input
                                    type="text"
                                    placeholder="wikipedia.org/chemistry"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    required
                                />
                            </label>

                            <label>
                                Context Note (optional)
                                <textarea
                                    placeholder="I need this for homework"
                                    value={context}
                                    onChange={(e) => setContext(e.target.value)}
                                />
                            </label>

                            <div className="grid2">
                                <label>
                                    Device ID
                                    <input
                                        type="text"
                                        value={deviceId}
                                        onChange={(e) => setDeviceId(e.target.value)}
                                        required
                                    />
                                </label>
                                <label>
                                    Age
                                    <input
                                        type="number"
                                        min="3"
                                        max="99"
                                        value={userAge}
                                        onChange={(e) => setUserAge(e.target.value)}
                                        required
                                    />
                                </label>
                            </div>

                            <button type="submit" disabled={loading}>{loading ? 'Requesting...' : 'Request Access'}</button>
                        </form>
                    </section>
                )}

                {decision && (
                    <section>
                        <h2>Decision Page</h2>
                        <div className="decision-card">
                            <div className="row">
                                <span className={VERDICT_STYLES[verdict] || 'badge'}>{verdict}</span>
                                <span className="mono">Score: {score}/100</span>
                            </div>

                            <div className="bar-wrap" aria-label="score bar">
                                <div className="bar-fill" style={{ width: scoreWidth(score) }} />
                            </div>

                            <p><strong>Reason:</strong> {decision.reason_text || 'No reason provided.'}</p>

                            <div className="row gap">
                                <button type="button" onClick={requestOverride} disabled={loading}>
                                    {loading ? 'Sending...' : 'Request Override'}
                                </button>
                                <button type="button" className="secondary" onClick={() => setDecision(null)}>
                                    New Request
                                </button>
                            </div>

                            {overrideNotice && (
                                <p className="ok">Parent has been notified.</p>
                            )}
                        </div>
                    </section>
                )}

                {error && <p className="error">{error}</p>}
            </div>
        </main>
    )
}
