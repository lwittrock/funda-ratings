import { useState, useEffect } from 'react';
import { Property, PropertiesData, ReviewStatus } from './types/property';
import PropertyCard from './components/PropertyCard';
import RatingModal from './components/RatingModal';
import Settings from './components/Settings';
import { supabase } from './lib/supabase';

function App() {
  const [properties, setProperties] = useState<PropertiesData>({});
  const [loading, setLoading] = useState(true);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [filterStatus, setFilterStatus] = useState<ReviewStatus>('new');
  const [menuOpen, setMenuOpen] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState<number | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [showSettings, setShowSettings] = useState(false);

  // Load data on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load all properties from Supabase
      const { data: propertiesData, error: propertiesError } = await supabase
        .from('properties')
        .select('*')
        .order('created_at', { ascending: false });

      if (propertiesError) throw propertiesError;

      // Convert array to object keyed by id
      const propertiesObj: PropertiesData = {};
      propertiesData?.forEach(prop => {
        propertiesObj[prop.id] = prop as Property;
      });
      setProperties(propertiesObj);

    } catch (error) {
      console.error('Error loading data:', error);
      alert('Error loading data from Supabase. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  const updateProperty = async (propertyId: number, updates: Partial<Property>) => {
    try {
      // Update in Supabase
      const { error } = await supabase
        .from('properties')
        .update({
          ...updates,
          updated_at: new Date().toISOString()
        })
        .eq('id', propertyId);

      if (error) throw error;

      // Update local state
      setProperties(prev => ({
        ...prev,
        [propertyId]: {
          ...prev[propertyId],
          ...updates,
          updated_at: new Date().toISOString()
        }
      }));
      
      setSelectedProperty(null);
    } catch (error) {
      console.error('Error updating property:', error);
      alert('Error saving changes. Check console for details.');
    }
  };

  const quickReject = async (propertyId: number, reason: string) => {
    await updateProperty(propertyId, {
      review_status: 'rejected',
      notes: reason || null
    });
    setShowRejectModal(null);
    setRejectReason('');
  };

  const getStatusCount = (status: ReviewStatus) => {
    return Object.values(properties).filter(p => p.review_status === status).length;
  };

  const filteredProperties = Object.values(properties).filter(prop => {
    return prop.review_status === filterStatus;
  });

  const statusConfig: Record<ReviewStatus, { label: string; icon: string }> = {
    new: { label: 'New', icon: '📋' },
    reviewed: { label: 'Reviewed', icon: '✓' },
    interested: { label: 'Interested', icon: '⭐' },
    rejected: { label: 'Rejected', icon: '✕' }
  };

  if (loading) {
    return (
      <div className="app">
        <div style={{ 
          minHeight: '100vh', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          fontSize: '1.25rem'
        }}>
          Loading properties...
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1 className="logo">🏠 Funda Tracker</h1>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button 
              className="btn-icon" 
              onClick={() => setShowSettings(true)}
              title="Settings"
              style={{ fontSize: '1.25rem' }}
            >
              ⚙️
            </button>
            <button className="menu-button" onClick={() => setMenuOpen(true)}>
              <span>{statusConfig[filterStatus].icon}</span>
              <span>{statusConfig[filterStatus].label}</span>
              <span>☰</span>
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Menu */}
      <div className={`menu-overlay ${menuOpen ? 'open' : ''}`} onClick={() => setMenuOpen(false)} />
      <div className={`mobile-menu ${menuOpen ? 'open' : ''}`}>
        <div className="menu-header">
          <span className="menu-title">Filter Properties</span>
          <button className="close-button" onClick={() => setMenuOpen(false)}>×</button>
        </div>
        <div className="status-filters">
          {(Object.keys(statusConfig) as ReviewStatus[]).map(status => (
            <button
              key={status}
              className={`status-button ${filterStatus === status ? 'active' : ''}`}
              onClick={() => {
                setFilterStatus(status);
                setMenuOpen(false);
              }}
            >
              <div className="status-info">
                <span className="status-icon">{statusConfig[status].icon}</span>
                <span className="status-label">{statusConfig[status].label}</span>
              </div>
              <span className="status-count">{getStatusCount(status)}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <main className="main-content">
        <div className="section-header">
          <h2 className="section-title">
            {statusConfig[filterStatus].icon} {statusConfig[filterStatus].label}
          </h2>
          <p className="section-subtitle">
            {filteredProperties.length} {filteredProperties.length === 1 ? 'property' : 'properties'}
          </p>
        </div>

        {filteredProperties.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <p>No properties in this category</p>
          </div>
        ) : (
          <div className="properties-grid">
            {filteredProperties.map(property => (
              <PropertyCard
                key={property.id}
                property={property}
                onReview={() => setSelectedProperty(property)}
                onQuickReject={() => setShowRejectModal(property.id)}
              />
            ))}
          </div>
        )}
      </main>

      {/* Rating Modal */}
      {selectedProperty && (
        <RatingModal
          property={selectedProperty}
          onSave={(updates) => updateProperty(selectedProperty.id, updates)}
          onClose={() => setSelectedProperty(null)}
        />
      )}

      {/* Quick Reject Modal */}
      {showRejectModal && (
        <div className="modal-overlay" onClick={() => setShowRejectModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-row">
                <h3 className="modal-title">Quick Reject</h3>
                <button className="modal-close" onClick={() => setShowRejectModal(null)}>×</button>
              </div>
              <p className="modal-subtitle">Optional: Why are you rejecting this property?</p>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <textarea
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  className="form-textarea"
                  placeholder="Too expensive, wrong location, etc..."
                />
              </div>
              <div className="modal-actions">
                <button onClick={() => quickReject(showRejectModal, rejectReason)} className="btn btn-danger">
                  Reject
                </button>
                <button onClick={() => {
                  setShowRejectModal(null);
                  setRejectReason('');
                }} className="btn btn-secondary">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      {showSettings && (
        <Settings onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}

export default App;