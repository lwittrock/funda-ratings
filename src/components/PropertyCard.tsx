import { Property } from '../types/property';
import { useState } from 'react';

interface PropertyCardProps {
  property: Property;
  onReview: () => void;
  onQuickReject: () => void;
}

export default function PropertyCard({ property, onReview, onQuickReject }: PropertyCardProps) {
  const [imageError, setImageError] = useState(false);

  const getAverageScore = (): number | null => {
    const scores = [
      property.rating_location,
      property.rating_quality,
      property.rating_value
    ].filter(s => s !== null) as number[];
    
    if (scores.length === 0) return null;
    return scores.reduce((a, b) => a + b, 0) / scores.length;
  };

  const avgScore = getAverageScore();

  return (
    <div className="property-card">
      {property.thumbnail_url && !imageError ? (
        <img 
          src={property.thumbnail_url} 
          alt={property.title}
          className="property-image"
          onError={() => setImageError(true)}
        />
      ) : (
        <div className="property-image-placeholder">🏠</div>
      )}
      
      <div className="property-content">
        <div className="property-header">
          <h3 className="property-title">{property.title}, {property.city}</h3>
        </div>
        
        <div className="property-price">
          € {property.price?.toLocaleString('nl-NL')}
        </div>
        
        <div className="property-stats">
          <div className="property-stat">
            <span className="stat-bullet">•</span>
            <span>{property.living_area} m² wonen</span>
          </div>
          {property.plot_area && (
            <div className="property-stat">
              <span className="stat-bullet">•</span>
              <span>{property.plot_area} m² perceel</span>
            </div>
          )}
          {property.bedrooms && (
            <div className="property-stat">
              <span className="stat-bullet">•</span>
              <span>{property.bedrooms} slaapkamers</span>
            </div>
          )}
          {property.energy_label && (
            <div className="property-stat">
              <span className="stat-bullet">•</span>
              <span>Energielabel {property.energy_label}</span>
            </div>
          )}
        </div>
        
        {avgScore !== null && (
          <div className="rating-display">
            <span className="rating-label">Average Score</span>
            <span className="rating-score">{avgScore.toFixed(1)}/5</span>
          </div>
        )}
        
        <div className="property-actions">
          <a href={property.url} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
            View on Funda
          </a>
          
          {property.review_status === 'new' ? (
            <>
              <button onClick={onReview} className="btn btn-success">
                Review
              </button>
              <button onClick={onQuickReject} className="btn btn-danger">
                ✕
              </button>
            </>
          ) : (
            <button onClick={onReview} className="btn btn-secondary">
              Edit
            </button>
          )}
        </div>
      </div>
    </div>
  );
}