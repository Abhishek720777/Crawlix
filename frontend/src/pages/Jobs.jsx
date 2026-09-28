import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { PlusCircle, Layers, Play, Pause, RotateCcw, X, Eye } from 'lucide-react';
import Navbar from '../components/Navbar';
import api from '../services/api';
import '../styles/jobs.css';

const Jobs = () => {
  const [jobs, setJobs] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // Form states
  const [name, setName] = useState('');
  const [targetUrls, setTargetUrls] = useState('');
  const [crawlerType, setCrawlerType] = useState('ecommerce');
  const [priority, setPriority] = useState('normal');
  const [maxPages, setMaxPages] = useState(25);
  const [maxDepth, setMaxDepth] = useState(2);
  const [customSelectors, setCustomSelectors] = useState('');

  const fetchJobs = async () => {
    try {
      const res = await api.get('/jobs');
      setJobs(res.data || []);
    } catch (err) {
      console.error('Failed to load jobs', err);
    }
  };

  useEffect(() => {
    fetchJobs();
    if (searchParams.get('action') === 'new') {
      setShowModal(true);
    }
    // Auto-refresh to show live job progress
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, [searchParams]);

  const handleCreateJob = async (e) => {
    e.preventDefault();
    const urls = targetUrls.split('\n').map(u => u.trim()).filter(Boolean);
    if (!name || urls.length === 0) return;

    let selectors = null;
    if (customSelectors) {
      try {
        selectors = JSON.parse(customSelectors);
      } catch (err) {
        alert('Invalid JSON in custom CSS selectors');
        return;
      }
    }

    try {
      await api.post('/jobs', {
        name,
        target_urls: urls,
        crawler_type: crawlerType,
        priority,
        max_pages: parseInt(maxPages),
        max_depth: parseInt(maxDepth),
        css_selectors: selectors
      });
      setShowModal(false);
      setName('');
      setTargetUrls('');
      fetchJobs();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to dispatch crawl job');
    }
  };

  const handleAction = async (jobId, action) => {
    try {
      await api.post(`/jobs/${jobId}/action?action=${action}`);
      fetchJobs();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="main-content">
      <Navbar title="Crawl Pipelines & Job Dispatcher" />
      <div className="page-wrapper">
        
        <div className="jobs-header">
          <div>
            <h2 className="section-title">Active & Completed Crawl Pipelines</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Create and orchestrate distributed extraction jobs across the worker pool
            </p>
          </div>
          <button className="btn-quick-new-job" onClick={() => setShowModal(true)}>
            <PlusCircle size={16} />
            <span>Launch Pipeline</span>
          </button>
        </div>

        {/* Jobs Table */}
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Pipeline Name</th>
                <th>Type</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Pages / Limit</th>
                <th>Extracted Records</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                    No crawl pipelines configured. Click "Launch Pipeline" above to create one.
                  </td>
                </tr>
              ) : (
                jobs.map((j) => (
                  <tr key={j.id}>
                    <td>
                      <strong>{j.name}</strong>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{j.target_urls?.[0]}</div>
                    </td>
                    <td><span style={{ textTransform: 'uppercase', fontSize: '0.8rem', fontWeight: 600 }}>{j.crawler_type}</span></td>
                    <td>{j.priority}</td>
                    <td>
                      <span className={`status-badge status-${j.status}`}>{j.status}</span>
                    </td>
                    <td>{j.pages_crawled} / {j.max_pages}</td>
                    <td><strong>{j.records_extracted}</strong></td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(j.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button 
                          style={{ background: 'transparent', color: 'var(--accent-secondary)' }}
                          onClick={() => navigate(`/data?jobId=${j.id}`)}
                          title="View Data"
                        >
                          <Eye size={16} />
                        </button>
                        {j.status === 'running' && (
                          <button 
                            style={{ background: 'transparent', color: 'var(--accent-warning)' }}
                            onClick={() => handleAction(j.id, 'pause')}
                            title="Pause"
                          >
                            <Pause size={16} />
                          </button>
                        )}
                        {j.status === 'paused' && (
                          <button 
                            style={{ background: 'transparent', color: 'var(--accent-success)' }}
                            onClick={() => handleAction(j.id, 'resume')}
                            title="Resume"
                          >
                            <Play size={16} />
                          </button>
                        )}
                        {(j.status === 'completed' || j.status === 'failed') && (
                          <button 
                            style={{ background: 'transparent', color: 'var(--accent-primary)' }}
                            onClick={() => handleAction(j.id, 'retry')}
                            title="Rerun"
                          >
                            <RotateCcw size={16} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Create Job Modal */}
        {showModal && (
          <div className="modal-overlay" onClick={() => setShowModal(false)}>
            <div className="modal-card" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3 className="modal-title">Launch Distributed Crawl Job</h3>
                <button style={{ background: 'transparent', color: 'var(--text-muted)' }} onClick={() => setShowModal(false)}>
                  <X size={20} />
                </button>
              </div>

              <form className="modal-form" onSubmit={handleCreateJob}>
                <div className="form-group">
                  <label>Pipeline Name</label>
                  <input
                    type="text"
                    placeholder="e.g., Global E-Commerce Pricing Monitor"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Seed Target URLs (One per line)</label>
                  <textarea
                    rows={3}
                    placeholder="https://books.toscrape.com&#10;https://quotes.toscrape.com"
                    value={targetUrls}
                    onChange={(e) => setTargetUrls(e.target.value)}
                    required
                  />
                </div>

                <div className="form-grid-2">
                  <div className="form-group">
                    <label>Intelligence / Crawler Type</label>
                    <select value={crawlerType} onChange={(e) => setCrawlerType(e.target.value)}>
                      <option value="ecommerce">E-Commerce & Pricing Intelligence</option>
                      <option value="news">News & Sentiment Extractor</option>
                      <option value="schema">Schema.org (JSON-LD) Ingestion</option>
                      <option value="generic">Generic Web Content & Links</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Queue Priority</label>
                    <select value={priority} onChange={(e) => setPriority(e.target.value)}>
                      <option value="high">High (Immediate Dispatch)</option>
                      <option value="normal">Normal (Scraping Pool)</option>
                      <option value="low">Low (Background Batch)</option>
                    </select>
                  </div>
                </div>

                <div className="form-grid-2">
                  <div className="form-group">
                    <label>Max Depth</label>
                    <input
                      type="number"
                      min="1"
                      max="5"
                      value={maxDepth}
                      onChange={(e) => setMaxDepth(e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label>Max Pages Limit</label>
                    <input
                      type="number"
                      min="1"
                      max="500"
                      value={maxPages}
                      onChange={(e) => setMaxPages(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Custom CSS Selectors (Optional JSON)</label>
                  <input
                    type="text"
                    placeholder='{"product_title": "h3 a", "price": ".price_color"}'
                    value={customSelectors}
                    onChange={(e) => setCustomSelectors(e.target.value)}
                  />
                </div>

                <button type="submit" className="btn-quick-new-job" style={{ padding: '12px', justifyContent: 'center', marginTop: '1rem' }}>
                  <span>Deploy to Celery Worker Pool</span>
                </button>
              </form>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default Jobs;
