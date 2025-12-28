import { useState, useEffect } from 'react';
import { Property, Rating, PropertiesData, RatingsData, ReviewStatus } from './types/property';
import PropertyCard from './components/PropertyCard';
import RatingModal from './components/RatingModal';
import { supabase } from './lib/supabase';

function App() {
  const [properties, setProperties] = useState<PropertiesData>({});
  const [ratings, setRatings] = useState<RatingsData>({});
  const [loading, setLoading] = useState(true);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [filterStatus, setFilterStatus] = useState<ReviewStatus>('unreviewed');
  const [menuOpen, setMenuOpen] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  // Load data on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load properties from Supabase
      const { data: propertiesData, error: propertiesError } = await supabase
        .from('properties')
        .select('*')
        .eq('status', 'active')
        .order('last_seen', { ascending: false });

      if (propertiesError) throw propertiesError;

      // Convert array to object keyed by id
      const propertiesObj: PropertiesData = {};
      propertiesData?.forEach(prop => {
        propertiesObj[prop.id] = prop as Property;
      });
      setProperties(propertiesObj);

      // Load ratings from Supabase
      const { data: ratingsData, error: ratingsError } = await supabase
        .from('ratings')
        .select('*');

      if (ratingsError) throw ratingsError;

      // Convert array to object keyed by property_id
      const ratingsObj: RatingsData = {};
      ratingsData?.forEach(rating => {
        ratingsObj[rating.property_id] = rating as Rating;
      });
      setRatings(ratingsObj);

    } catch (error) {
      console.error('Error loading data:', error);
      alert('Error loading data from Supabase. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  const updateRating = async (rating: Rating) => {
    try {
      // Upsert to Supabase
      const { error } = await supabase
        .from('ratings')
        .upsert({
          property_id: rating.property_id,
          status: rating.status,
          location_score: rating.location_score,
          house_quality_score: rating.house_quality_score,
          garden_score: rating.garden_score,
          value_score: rating.value_score,
          notes: rating.notes,
          rejection_reason: rating.rejection_reason,
          reviewed_date: rating.reviewed_date,
          updated_date: rating.updated_date,
        }, {
          onConflict: 'property_id'
        });

      if (error) throw error;

      // Update local state
      setRatings(prev => ({ ...prev, [rating.property_id]: rating }));
      setSelectedProperty(null);
    } catch (error) {
      console.error('Error saving rating:', error);
      alert('Error saving rating. Check console for details.');
    }
  };

  const quickReject = async (propertyId: string, reason: string) => {
    const now = new Date().toISOString();
    const rating: Rating = {
      property_id: propertyId,
      status: 'rejected',
      location_score: null,
      house_quality_score: null,
      garden_score: null,
      value_score: null,
      notes: '',
      rejection_reason: reason,
      reviewed_date: now,
      updated_date: now,
    };
    await updateRating(rating);
    setShowRejectModal(null);
    setRejectReason('');
  };

  const getPropertyStatus = (propertyId: string): ReviewStatus => {
    return ratings[propertyId]?.status || 'unreviewed';
  };

  const getStatusCount = (status: ReviewStatus) => {
    return Object.values(properties).filter(
      p => p.status === 'active' && getPropertyStatus(p.id) === status
    ).length;
  };

  const filteredProperties = Object.values(properties).filter(prop => {
    if (prop.status !== 'active') return false;
    return getPropertyStatus(prop.id) === filterStatus;
  });

  const statusConfig: Record<ReviewStatus, { label: string; icon: string }> = {
    unreviewed: { label: 'Unreviewed', icon: '📋' },
    reviewed: { label: 'Reviewed', icon: '✓' },
    viewing_interest: { label: 'Viewing Interest', icon: '⭐' },
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
          <button className="menu-button" onClick={() => setMenuOpen(true)}>
            <span>{statusConfig[filterStatus].icon}</span>
            <span>{statusConfig[filterStatus].label}</span>
            <span>☰</span>
          </button>
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
                rating={ratings[property.id]}
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
          existingRating={ratings[selectedProperty.id]}
          onSave={updateRating}
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
    </div>
  );
}

export default App;