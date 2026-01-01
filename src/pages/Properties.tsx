import { useState, useEffect, useMemo } from 'react';
import { Property, PropertiesData, ReviewStatus } from '../types/property';
import PropertyCard from '../components/PropertyCard';
import RatingModal from '../components/RatingModal';
import { supabase } from '../lib/supabase';

const statusConfig: Record<ReviewStatus, { label: string }> = {
  new: { label: 'New' },
  reviewed: { label: 'Reviewed' },
  interested: { label: 'Interested' },
  rejected: { label: 'Rejected' }
};

export default function Properties() {
  const [properties, setProperties] = useState<PropertiesData>({});
  const [loading, setLoading] = useState(true);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [filterStatus, setFilterStatus] = useState<ReviewStatus>('new');
  const [showRejectModal, setShowRejectModal] = useState<number | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      const { data: propertiesData, error: propertiesError } = await supabase
        .from('properties')
        .select('*')
        .order('created_at', { ascending: false });

      if (propertiesError) throw propertiesError;

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
      const { error } = await supabase
        .from('properties')
        .update({
          ...updates,
          updated_at: new Date().toISOString()
        })
        .eq('id', propertyId);

      if (error) throw error;

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

  const filteredProperties = useMemo(() => {
    return Object.values(properties).filter(prop => prop.review_status === filterStatus);
  }, [properties, filterStatus]);

  if (loading) {
    return (
      <div style={{ 
        minHeight: '80vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        fontSize: '1.25rem',
        color: 'var(--text-secondary)'
      }}>
        Loading properties...
      </div>
    );
  }

  return (
    <div className="main-content">
      {/* Filter Buttons */}
      <div className="filter-buttons">
        {(Object.keys(statusConfig) as ReviewStatus[]).map(status => (
          <button
            key={status}
            onClick={() => setFilterStatus(status)}
            className={`filter-button ${filterStatus === status ? 'active' : ''}`}
          >
            <span className="filter-label">{statusConfig[status].label}</span>
            {/* <span className="filter-count">({getStatusCount(status)})</span> */}
          </button>
        ))}
      </div>

      {/* Section Header */}
      <div className="section-header">
        <h2 className="section-title">
          {statusConfig[filterStatus].label}
        </h2>
        <p className="section-subtitle">
          {filteredProperties.length} {filteredProperties.length === 1 ? 'property' : 'properties'}
        </p>
      </div>

      {/* Properties Grid */}
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
    </div>
  );
}