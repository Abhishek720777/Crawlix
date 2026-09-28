import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Layers, 
  Database, 
  Cpu, 
  Server, 
  CheckCircle2, 
  AlertTriangle,
  Clock, 
  TrendingUp,
  Globe,
  Wifi,
  WifiOff
} from 'lucide-react';
import Navbar from '../components/Navbar';
import api from '../services/api';
import '../styles/dashboard.css';

const statusColor = {
  active:   'var(--accent-success)',
  idle:     'var(--accent-primary)',
  offline:  'var(--text-muted)',
  error:    '#ef4444',
};

const jobStatusColor = {
  completed: 'var(--accent-success)',
  running:   'var(--accent-primary)',
  pending:   'var(--accent-purple)',
  failed:    '#ef4444',
  paused:    '#f59e0b',
  cancelled: 'var(--text-muted)',
};

const Dashboard = () => {
  const [stats, setStats] = useState({
    activeJobs: 0,
    completedJobs: 0,
    totalRecords: 0,
    workerNodes: 0,
    onlineNodes: 0,
    meshHealth: '—',
    avgLatency: '—',
  });
  const [nodes, setNodes] = useState([]);
  const [recentJobs, setRecentJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [jobsRes, nodesRes] = await Promise.all([
          api.get('/jobs'),
          api.get('/nodes'),
        ]);

        const jobs = jobsRes.data || [];
        const nodeList = nodesRes.data || [];

        // --- Real stat computations ---
        const running   = jobs.filter(j => j.status === 'running').length;
        const completed = jobs.filter(j => j.status === 'completed').length;
        const totalRecs = jobs.reduce((acc, j) => acc + (j.records_extracted || 0), 0);

        // Online = nodes that have "active" or "idle" status
        const onlineNodes = nodeList.filter(n => n.status === 'active' || n.status === 'idle').length;
        const meshHealth  = nodeList.length === 0
          ? '—'
          : `${Math.round((onlineNodes / nodeList.length) * 100)}%`;

        // Average response latency from node records (response_time_ms isn't on nodes,
        // so we compute average from the most recent scraped records via jobs data)
        // Proxy: use avg cpu_usage of active nodes as a throughput indicator instead
        const activeCpus = nodeList.filter(n => n.status === 'active').map(n => n.cpu_usage || 0);
        const avgCpu     = activeCpus.length
          ? (activeCpus.reduce((a, b) => a + b, 0) / activeCpus.length).toFixed(1)
          : null;

        setStats({
          activeJobs:    running,
          completedJobs: completed,
          totalRecords:  totalRecs,
          workerNodes:   nodeList.length,
          onlineNodes,
          meshHealth,
          avgCpu: avgCpu !== null ? `${avgCpu}%` : '—',
        });

        setRecentJobs(jobs.slice(0, 6));
        setNodes(nodeList);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="main-content">
      <Navbar title="Distributed Cluster Operations" />
      <div className="page-wrapper">

        {/* Stat Cards Grid */}
        <div className="dashboard-grid">

          <div className="stat-card">
            <div className="stat-icon-wrapper" style={{ color: 'var(--accent-primary)' }}>
              <Layers size={24} />
            </div>
            <div className="stat-info">
              <span className="stat-label">Active Crawl Jobs</span>
              <span className="stat-value">{loading ? '…' : stats.activeJobs}</span>
              <span className="stat-subtext">
                {stats.completedJobs > 0 ? `${stats.completedJobs} completed` : 'No completed jobs yet'}
              </span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon-wrapper" style={{ color: 'var(--accent-secondary)' }}>
              <Database size={24} />
            </div>
            <div className="stat-info">
              <span className="stat-label">Records Ingested</span>
              <span className="stat-value">{loading ? '…' : stats.totalRecords.toLocaleString()}</span>
              <span className="stat-subtext">
                {stats.totalRecords === 0 ? 'No data yet — launch a pipeline' : 'Across all your jobs'}
              </span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon-wrapper" style={{ color: 'var(--accent-success)' }}>
              <Server size={24} />
            </div>
            <div className="stat-info">
              <span className="stat-label">Online Worker Nodes</span>
              <span className="stat-value">
                {loading ? '…' : `${stats.onlineNodes}/${stats.workerNodes}`}
              </span>
              <span className="stat-subtext">
                Mesh health: {loading ? '…' : stats.meshHealth}
              </span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon-wrapper" style={{ color: 'var(--accent-purple)' }}>
              <Cpu size={24} />
            </div>
            <div className="stat-info">
              <span className="stat-label">Active Node Avg CPU</span>
              <span className="stat-value">{loading ? '…' : stats.avgCpu}</span>
              <span className="stat-subtext">
                {stats.onlineNodes > 0 ? `Across ${stats.onlineNodes} active workers` : 'No active workers'}
              </span>
            </div>
          </div>

        </div>

        {/* Multi-Column Section */}
        <div className="dashboard-sections">

          {/* Recent Pipelines */}
          <div className="panel-card">
            <h2 className="section-title">
              <Activity size={20} color="var(--accent-primary)" />
              <span>Recent Ingestion Pipelines</span>
            </h2>

            {loading ? (
              <p style={{ color: 'var(--text-muted)', padding: '1rem 0' }}>Loading…</p>
            ) : recentJobs.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', padding: '1rem 0' }}>
                No jobs found. Create your first crawl pipeline to start ingesting data.
              </p>
            ) : (
              <div className="node-list">
                {recentJobs.map((job) => (
                  <div key={job.id} className="node-item">
                    <div className="node-item-meta">
                      <div
                        className="node-status-indicator"
                        style={{ background: jobStatusColor[job.status] || 'var(--text-muted)' }}
                      />
                      <div>
                        <div className="node-hostname">{job.name}</div>
                        <div className="node-specs">
                          {job.crawler_type.toUpperCase()} • {job.target_urls?.[0]}
                        </div>
                      </div>
                    </div>
                    <div className="node-metrics">
                      <span><strong>{job.records_extracted ?? 0}</strong> records</span>
                      <span
                        style={{
                          color: jobStatusColor[job.status] || 'var(--text-muted)',
                          fontWeight: 600,
                          textTransform: 'capitalize'
                        }}
                      >
                        {job.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Worker Node Telemetry */}
          <div className="panel-card">
            <h2 className="section-title">
              <Server size={20} color="var(--accent-secondary)" />
              <span>Worker Node Mesh</span>
            </h2>

            {loading ? (
              <p style={{ color: 'var(--text-muted)', padding: '1rem 0' }}>Loading…</p>
            ) : nodes.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', padding: '1rem 0' }}>
                No worker nodes registered yet.
              </p>
            ) : (
              <div className="node-list">
                {nodes.map((n) => (
                  <div key={n.id} className="node-item">
                    <div className="node-item-meta">
                      <div
                        className="node-status-indicator"
                        style={{ background: statusColor[n.status] || 'var(--text-muted)' }}
                      />
                      <div>
                        <div className="node-hostname">
                          {n.hostname || n.id}
                          {n.status === 'offline' && (
                            <WifiOff
                              size={13}
                              style={{ marginLeft: 6, color: 'var(--text-muted)', verticalAlign: 'middle' }}
                            />
                          )}
                        </div>
                        <div className="node-specs">
                          {n.ip_address ? `IP: ${n.ip_address} • ` : ''}
                          Slots: {n.concurrency} • 
                          Tasks done: {n.completed_tasks ?? 0}
                        </div>
                      </div>
                    </div>
                    <div className="node-metrics">
                      <span>CPU: <strong>{n.cpu_usage ?? '—'}%</strong></span>
                      <span>RAM: <strong>{n.memory_usage ?? '—'}%</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
};

export default Dashboard;
