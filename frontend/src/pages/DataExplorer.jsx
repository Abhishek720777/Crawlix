import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Database, Download, FileSpreadsheet, FileJson, ExternalLink, Search } from 'lucide-react';
import Navbar from '../components/Navbar';
import api from '../services/api';
import '../styles/data_explorer.css';

const DataExplorer = () => {
  const [searchParams] = useSearchParams();
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(searchParams.get('jobId') || '');
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const loadJobs = async () => {
      try {
        const res = await api.get('/jobs');
        const list = res.data || [];
        setJobs(list);
        if (!selectedJobId && list.length > 0) {
          setSelectedJobId(list[0].id);
        }
      } catch (err) {
        console.error(err);
      }
    };
    loadJobs();
  }, []);

  const fetchRecords = async (jobId) => {
    setLoading(true);
    try {
      const url = jobId ? `/data/records?job_id=${jobId}&limit=100` : '/data/records?limit=100';
      const res = await api.get(url);
      setRecords(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords(selectedJobId);
  }, [selectedJobId]);

  const handleExport = (format) => {
    if (!selectedJobId) return;
    const token = localStorage.getItem('crawlix_token');
    const exportUrl = `${api.defaults.baseURL}/data/export?job_id=${selectedJobId}&format=${format}`;
    window.open(exportUrl, '_blank');
  };

  const filteredRecords = records.filter(r => 
    r.url.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (r.page_title && r.page_title.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="main-content">
      <Navbar title="Structured Data & Record Explorer" />
      <div className="page-wrapper">
        
        <div className="data-explorer-controls">
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            <select 
              value={selectedJobId} 
              onChange={(e) => setSelectedJobId(e.target.value)}
              style={{ minWidth: '220px' }}
            >
              <option value="">All Scraped Records</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>{j.name}</option>
              ))}
            </select>

            <div style={{ position: 'relative' }}>
              <input
                type="text"
                placeholder="Filter by URL or title..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ width: '260px' }}
              />
            </div>
          </div>

          <div className="data-export-buttons">
            <button className="btn-export" onClick={() => handleExport('csv')}>
              <FileSpreadsheet size={16} color="var(--accent-success)" />
              <span>Export CSV</span>
            </button>
            <button className="btn-export" onClick={() => handleExport('json')}>
              <FileJson size={16} color="var(--accent-secondary)" />
              <span>Export JSON</span>
            </button>
          </div>
        </div>

        {/* Data Table */}
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Target URL & Title</th>
                <th>HTTP Status</th>
                <th>Latency</th>
                <th>Structured Data Payload</th>
                <th>Worker Node</th>
                <th>Ingested At</th>
              </tr>
            </thead>
            <tbody>
              {filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                    No scraped records available for this selection.
                  </td>
                </tr>
              ) : (
                filteredRecords.map((rec) => (
                  <tr key={rec.id}>
                    <td style={{ maxWidth: '280px' }}>
                      <strong style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {rec.page_title || 'Untitled Document'}
                      </strong>
                      <a 
                        href={rec.url} 
                        target="_blank" 
                        rel="noreferrer" 
                        style={{ fontSize: '0.75rem', color: 'var(--accent-secondary)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                      >
                        <span style={{ maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {rec.url}
                        </span>
                        <ExternalLink size={12} />
                      </a>
                    </td>
                    <td>
                      <span className={`status-badge ${rec.http_status === 200 ? 'status-completed' : 'status-failed'}`}>
                        {rec.http_status}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{rec.response_time_ms} ms</td>
                    <td style={{ maxWidth: '300px' }}>
                      <pre className="json-preview-card">
                        {JSON.stringify(rec.structured_data || {}, null, 2)}
                      </pre>
                    </td>
                    <td style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {rec.worker_node}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(rec.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
};

export default DataExplorer;
