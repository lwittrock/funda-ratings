import { useState } from 'react';
import { Property, ReviewStatus } from '../types/property';

interface RatingModalProps {
  property: Property;
  onSave: (updates: Partial<Property>) => void;
  onClose: () => void;
}

export default function RatingModal({ property, onSave, onClose }: RatingModalProps) {
  const [locationScore, setLocationScore] = useState(property.rating_location || 0);
  const [qualityScore, setQualityScore] = useState(property.rating_quality || 0);
  const [valueScore, setValueScore] = useState(property.rating_value || 0);
  const [status, setStatus] = useState<ReviewStatus>(property.status);
  const [notes, setNotes] = useState(property.notes || '');

  const handleSave = () => {
    onSave({
      status,
      rating_location: locationScore || null,
      rating_quality: qualityScore || null,
      rating_value: valueScore || null,
      notes: notes || null,
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <div>
              <h3 className="modal-title">{property.title}</h3>
              <p className="modal-subtitle">{property.address}</p>
              <p className="modal-subtitle" style={{ fontWeight: 600, marginTop: '0.5rem' }}>
                € {property.price?.toLocaleString('nl-NL')} k.k.
              </p>
            </div>
            <button className="modal-close" onClick={onClose}>×</button>
          </div>
          <div style={{ marginTop: '0.75rem' }}>
            <a href={property.url} target="_blank" rel="noopener noreferrer" className="link">
              Open on Funda →
            </a>
          </div>
        </div>
        
        <div className="modal-body">
          <div className="form-group">
            <label className="form-label">Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value as ReviewStatus)} className="form-select">
              <option value="reviewed">Reviewed</option>
              <option value="interested">Interested</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          
          {status !== 'rejected' && (
            <>
              <div className="slider-group">
                <div className="slider-header">
                  <label className="form-label" style={{ margin: 0 }}>Location</label>
                  <span className="slider-value">{locationScore ? `${locationScore}/5` : '—'}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="5"
                  value={locationScore}
                  onChange={(e) => setLocationScore(Number(e.target.value))}
                  className="slider"
                />
                <div className="slider-ticks">
                  <span>0</span>
                  <span>1</span>
                  <span>2</span>
                  <span>3</span>
                  <span>4</span>
                  <span>5</span>
                </div>
              </div>
              
              <div className="slider-group">
                <div className="slider-header">
                  <label className="form-label" style={{ margin: 0 }}>House Quality</label>
                  <span className="slider-value">{qualityScore ? `${qualityScore}/5` : '—'}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="5"
                  value={qualityScore}
                  onChange={(e) => setQualityScore(Number(e.target.value))}
                  className="slider"
                />
                <div className="slider-ticks">
                  <span>0</span>
                  <span>1</span>
                  <span>2</span>
                  <span>3</span>
                  <span>4</span>
                  <span>5</span>
                </div>
              </div>
              
              <div className="slider-group">
                <div className="slider-header">
                  <label className="form-label" style={{ margin: 0 }}>Value for Money</label>
                  <span className="slider-value">{valueScore ? `${valueScore}/5` : '—'}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="5"
                  value={valueScore}
                  onChange={(e) => setValueScore(Number(e.target.value))}
                  className="slider"
                />
                <div className="slider-ticks">
                  <span>0</span>
                  <span>1</span>
                  <span>2</span>
                  <span>3</span>
                  <span>4</span>
                  <span>5</span>
                </div>
              </div>
            </>
          )}
          
          <div className="form-group">
            <label className="form-label">Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="form-textarea"
              placeholder="Your thoughts about this property..."
            />
          </div>
          
          <div className="modal-actions">
            <button onClick={handleSave} className="btn btn-success">
              Save Rating
            </button>
            <button onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}