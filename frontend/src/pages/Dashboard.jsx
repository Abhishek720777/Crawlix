import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Layers, 
  Database, 
  Cpu, 
  Server, 
  CheckCircle2, 
  Clock, 
  ArrowUpRight,
  TrendingUp,
  Globe
} from 'lucide-react';
import Navbar from '../components/Navbar';
import api from '../services/api';
import '../styles/dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState({
    activeJobs: 0,
    totalRecords: 0,
    workerNodes: 3,
    avgLatency: '142ms',
  });
  const [nodes, setNodes] = useState([]);
  const [recentJobs, setRecentJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [jobsRes, nodesRes, recordsRes] = await Promise.all([
          api.get('/jobs'),
          api.get('/nodes'),
          api.get('/data/records?limit=10')
        ]);

        const jobs = jobsRes.data || [];
        const nodeList = nodesRes.data || [];
        const records = recordsRes.data || [];

        const running = jobs.filter(j => j.status === 'running').length;
        const totalRecs = jobs.reduce((acc, j) => acc + (j.records_extracted || 0), 0);

        setStats({
          activeJobs: running,
          totalRecords: totalRecs || records.length,
          workerNodes: nodeList.length,
          avgLatency: '118ms'
        });

        setRecentJobs(jobs.slice(0, 5));
        setNodes(nodeList);
      } catch (err) {
        console.error('Failed to load dashboard telemetry:', err);
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
              <span className="stat-value">{stats.activeJobs}</span>
              <span className="stat-subtext">Distributed across queues</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon-wrapper" style={{ color: 'var(--accent-secondary)' }}>
              <Database size={24} />
            </div>
            <div className="stat-info">
              <span className="stat-label">Records Ingested</span>
              <span className="stat-value">{stats.totalRecords.toLocaleString()}</span>
              <span className="stat-subtext">+18.4% this session</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon-wrapper" style={{ color: 'var(--accent-success)' }}>
              <Server size={24} />
            </div>
            <div className="stat-info">
              <span className="stat-label">Online Worker Nodes</span>
              <span className="stat-value">{stats.workerNodes}</span>
              <span className="stat-subtext">100% mesh health</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon-wrapper" style={{ color: 'var(--accent-purple)' }}>
              <Cpu size={24} />
            </div>
            <div className="stat-info">
              <span className="stat-label">Avg Extraction Latency</span>
              <span className="stat-value">{stats.avgLatency}</span>
              <span className="stat-subtext">High concurrency throughput</span>
            </div>
          </div>
        </div>

        {/* Multi-Column Section */}
        <div className="dashboard-sections">
          
          {/* Active Pipelines */}
          <div className="panel-card">
            <h2 className="section-title">
              <Activity size={20} color="var(--accent-primary)" />
              <span>Recent Ingestion Pipelines</span>
            </h2>

            {recentJobs.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', padding: '1rem 0' }}>
                No active jobs found. Create your first crawl pipeline to start ingesting data.
              </p>
            ) : (
              <div className="node-list">
                {recentJobs.map((job) => (
                  <div key={job.id} className="node-item">
                    <div className="node-item-meta">
                      <div 
                        className="node-status-indicator" 
                        style={{ background: job.status === 'completed' ? 'var(--accent-success)' : 'var(--accent-primary)' }}
                      />
                      <div>
                        <div className="node-hostname">{job.name}</div>
                        <div className="node-specs">{job.crawler_type.toUpperCase()} • {job.target_urls?.[0]}</div>
                      </div>
                    </div>

                    <div className="node-metrics">
                      <span><strong>{job.records_extracted}</strong> records</span>
                      <span><strong>{job.status}</strong></span>
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

            <div className="node-list">
              {nodes.map((n) => (
                <div key={n.id} className="node-item">
                  <div className="node-item-meta">
                    <div className="node-status-indicator" />
                    <div>
                      <div className="node-hostname">{n.hostname || n.id}</div>
                      <div className="node-specs">IP: {n.ip_address} • Slots: {n.concurrency}</div>
                    </div>
                  </div>
                  <div className="node-metrics">
                    <span>CPU: {n.cpu_usage}%</span>
                    <span>RAM: {n.memory_usage}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};

export default Dashboard;
