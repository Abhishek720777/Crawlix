import React, { useState, useEffect } from 'react';
import { Network, Server, Cpu, HardDrive, RefreshCw, Zap, Shield } from 'lucide-react';
import Navbar from '../components/Navbar';
import api from '../services/api';
import '../styles/node_mesh.css';

const NodeMesh = () => {
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchNodes = async () => {
    try {
      const res = await api.get('/nodes');
      setNodes(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNodes();
    const interval = setInterval(fetchNodes, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="main-content">
      <Navbar title="Worker Mesh Topology" />
      <div className="page-wrapper">
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 className="section-title">Distributed Node Infrastructure</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Real-time telemetry, load balancing, and health diagnostics across your Celery crawler workers
            </p>
          </div>
          <button 
            className="btn-quick-new-job" 
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)' }}
            onClick={fetchNodes}
          >
            <RefreshCw size={16} />
            <span>Poll Cluster</span>
          </button>
        </div>

        <div className="mesh-topology-grid">
          {nodes.map((node) => (
            <div key={node.id} className="node-card">
              <div className="node-card-header">
                <div className="node-title-group">
                  <Server size={20} color="var(--accent-secondary)" />
                  <span className="node-title">{node.hostname || node.id}</span>
                </div>
                <div className="system-status-pill">
                  <span className="status-dot"></span>
                  <span>{node.status.toUpperCase()}</span>
                </div>
              </div>

              {/* CPU Usage Bar */}
              <div className="node-progress-bar-container">
                <div className="progress-label-row">
                  <span><Cpu size={12} style={{ marginRight: '4px' }} /> CPU Utilization</span>
                  <span>{node.cpu_usage}%</span>
                </div>
                <div className="progress-track">
                  <div 
                    className="progress-fill" 
                    style={{ 
                      width: `${Math.min(node.cpu_usage, 100)}%`, 
                      background: node.cpu_usage > 80 ? 'var(--accent-danger)' : 'var(--accent-primary)' 
                    }}
                  />
                </div>
              </div>

              {/* Memory Usage Bar */}
              <div className="node-progress-bar-container">
                <div className="progress-label-row">
                  <span><HardDrive size={12} style={{ marginRight: '4px' }} /> Memory Ingestion</span>
                  <span>{node.memory_usage}%</span>
                </div>
                <div className="progress-track">
                  <div 
                    className="progress-fill" 
                    style={{ 
                      width: `${Math.min(node.memory_usage, 100)}%`, 
                      background: 'var(--accent-secondary)' 
                    }}
                  />
                </div>
              </div>

              {/* Footer specs */}
              <div className="node-stats-footer">
                <div>IP: <strong>{node.ip_address || '10.0.4.12'}</strong></div>
                <div>Slots: <strong>{node.concurrency} threads</strong></div>
                <div>Tasks Done: <strong>{node.completed_tasks}</strong></div>
                <div>Active: <strong>{node.active_tasks}</strong></div>
              </div>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
};

export default NodeMesh;
