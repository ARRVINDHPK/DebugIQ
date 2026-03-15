import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, ScatterChart, Scatter, ZAxis
} from 'recharts';
import { 
  AlertCircle, CheckCircle, Info, Activity, Flag, Clock, Layout, 
  Download, Filter, ChevronDown, Monitor
} from 'lucide-react';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];
const SEVERITY_COLORS = {
  FATAL: '#f85149',
  ERROR: '#d73a49',
  WARNING: '#d29922',
  INFO: '#58a6ff'
};

function App() {
  const [failures, setFailures] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedFailureId, setSelectedFailureId] = useState(null);
  const [topN, setTopN] = useState(15);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [fRes, sRes] = await Promise.all([
        axios.get('/api/failures'),
        axios.get('/api/summary')
      ]);
      setFailures(fRes.data);
      setSummary(sRes.data);
      if (fRes.data.length > 0) {
        setSelectedFailureId(0);
      }
      setLoading(false);
    } catch (err) {
      console.error("Error fetching data:", err);
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading DebugIQ Dashboard...</div>;
  if (!failures.length) return <div className="no-data">No failures found. Run the analysis pipeline first.</div>;

  const selectedFailure = failures[selectedFailureId] || failures[0];

  // Data preparation for charts
  const catData = Object.entries(failures.reduce((acc, f) => {
    acc[f.category] = (acc[f.category] || 0) + 1;
    return acc;
  }, {})).map(([name, value]) => ({ name, value }));

  const modData = summary?.problematic_modules || [];

  const clusterData = Object.entries(failures.reduce((acc, f) => {
    if (!acc[f.cluster_id]) acc[f.cluster_id] = { id: f.cluster_id, count: 0, priority: 0 };
    acc[f.cluster_id].count += 1;
    acc[f.cluster_id].priority += f.priority_score;
    return acc;
  }, {})).map(([id, data]) => ({
    id: `Cluster ${id}`,
    count: data.count,
    priority: (data.priority / data.count).toFixed(2)
  }));

  const timelineData = failures
    .filter(f => f.timestamp_parsed)
    .sort((a, b) => new Date(a.timestamp_parsed) - new Date(b.timestamp_parsed))
    .map(f => ({
      time: new Date(f.timestamp_parsed).getTime(),
      priority: f.priority_score,
      severity: f.severity,
      module: f.module
    }));

  const knownBugs = failures.filter(f => f.known_bug_flag === 1);

  return (
    <div className="app-container">
      {/* 10. Sidebar: Debug Report Download */}
      <aside className="sidebar">
        <h2>DebugIQ</h2>
        <div className="sidebar-section">
          <h3>Reports</h3>
          <a href="http://localhost:5000/api/report/debug_report.txt" className="download-btn">
            <Download size={16} style={{marginRight: '8px'}} />
            Text Report
          </a>
          <a href="http://localhost:5000/api/report/debug_report.md" className="download-btn">
            <Download size={16} style={{marginRight: '8px'}} />
            Markdown Report
          </a>
        </div>
        <div className="sidebar-footer">
          <Monitor size={14} /> v1.0.0-react
        </div>
      </aside>

      <main className="main-content">
        <header className="header">
          <h1>🔍 Log Intelligence Dashboard</h1>
        </header>

        {/* 1. Regression Overview */}
        <section className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{summary?.regression_health_score}/100</div>
            <div className="stat-label">Health Score</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{failures.length}</div>
            <div className="stat-label">Total Failures</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{new Set(failures.map(f => f.failure_signature)).size}</div>
            <div className="stat-label">Unique Failures</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{color: SEVERITY_COLORS.FATAL}}>
              {failures.filter(f => ['FATAL', 'ERROR'].includes(f.severity)).length}
            </div>
            <div className="stat-label">Critical Issues</div>
          </div>
        </section>

        <div className="grid-2x2">
          {/* 3. Failure Category Distribution */}
          <div className="chart-card">
            <h3>3. Failure Category Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={catData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={80} label>
                  {catData.map((entry, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* 5. Module Hotspot Analysis */}
          <div className="chart-card">
            <h3>5. Module Hotspot Analysis</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={modData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                <XAxis dataKey="module" stroke="#8b949e" />
                <YAxis stroke="#8b949e" />
                <Tooltip contentStyle={{backgroundColor: '#1d232c', border: '1px solid #30363d'}} />
                <Bar dataKey="failures" fill="#f85149" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* 4. Failure Clusters */}
          <div className="chart-card">
            <h3>4. Failure Clusters</h3>
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                <XAxis dataKey="count" name="Count" stroke="#8b949e" />
                <YAxis dataKey="priority" name="Avg Priority" stroke="#8b949e" />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{backgroundColor: '#1d232c', border: '1px solid #30363d'}} />
                <Scatter name="Clusters" data={clusterData} fill="#58a6ff" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          {/* 6. Failure Timeline */}
          <div className="chart-card">
            <h3>6. Failure Timeline</h3>
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                <XAxis type="number" dataKey="time" name="Time" domain={['auto', 'auto']} tickFormatter={(t) => new Date(t).toLocaleTimeString()} stroke="#8b949e" />
                <YAxis dataKey="priority" name="Priority" stroke="#8b949e" />
                <Tooltip contentStyle={{backgroundColor: '#1d232c', border: '1px solid #30363d'}} />
                <Scatter data={timelineData} fill="#d29922" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 2. Failure Priority Ranking */}
        <section className="table-container">
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px'}}>
            <h3>2. Failure Priority Ranking</h3>
            <div>
              <Filter size={16} style={{marginRight: '8px', verticalAlign: 'middle'}} />
              <select value={topN} onChange={(e) => setTopN(parseInt(e.target.value))} style={{backgroundColor: '#161b22', color: 'white', border: '1px solid #30363d', borderRadius: '4px', padding: '4px'}}>
                <option value={10}>Top 10</option>
                <option value={20}>Top 20</option>
                <option value={50}>Top 50</option>
              </select>
            </div>
          </div>
          <table>
            <thead>
              <tr>
                <th>Severity</th>
                <th>Module</th>
                <th>Category</th>
                <th>Score</th>
                <th>Freq</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {failures.sort((a,b) => b.priority_score - a.priority_score).slice(0, topN).map((f, i) => (
                <tr key={i} onClick={() => setSelectedFailureId(failures.indexOf(f))} style={{cursor: 'pointer', backgroundColor: selectedFailure === f ? 'rgba(88, 166, 255, 0.1)' : 'transparent'}}>
                  <td style={{color: SEVERITY_COLORS[f.severity], fontWeight: 'bold'}}>{f.severity}</td>
                  <td>{f.module}</td>
                  <td>{f.category}</td>
                  <td>{f.priority_score.toFixed(1)}</td>
                  <td>{f.frequency}</td>
                  <td><button onClick={() => setSelectedFailureId(failures.indexOf(f))} style={{padding: '4px 8px', fontSize: '0.8rem', cursor: 'pointer'}}>Analyze</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* 7 & 8. Root Cause & Recommendations */}
        <section className="action-section">
          <div className="action-card info">
            <h3>7. Root Cause Suggestion</h3>
            <div style={{marginBottom: '10px', fontSize: '0.9rem', color: 'var(--text-muted)'}}>
              For: {selectedFailure?.module} - {selectedFailure?.category}
            </div>
            <p>{selectedFailure?.root_cause_suggestion || "Select a failure above to see suggestions."}</p>
          </div>
          <div className="action-card success">
            <h3>8. Debug Recommendations</h3>
            <div style={{marginBottom: '10px', fontSize: '0.9rem', color: 'var(--text-muted)'}}>
              Recommended actions
            </div>
            <p>{selectedFailure?.debug_actions || "Select a failure above to see recommendations."}</p>
          </div>
        </section>

        {/* 9. Known Bug Detection */}
        <section className="table-container">
          <h3>9. Known Bug Detection</h3>
          {knownBugs.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Module</th>
                  <th>Category</th>
                  <th>Message</th>
                  <th>Frequency</th>
                </tr>
              </thead>
              <tbody>
                {knownBugs.map((f, i) => (
                  <tr key={i}>
                    <td>{f.module}</td>
                    <td>{f.category}</td>
                    <td>{f.message}</td>
                    <td>{f.frequency}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{color: 'var(--text-muted)'}}>No known bugs detected in this run.</p>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
