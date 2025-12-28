import { Property, Rating } from '../types/property';
import { useState } from 'react';

interface PropertyCardProps {
  property: Property;
  rating?: Rating;
  onReview: () => void;
  onQuickReject: () => void;
}

export default function PropertyCard({ property, rating, onReview, onQuickReject }: PropertyCardProps) {
  const [imageError, setImageError] = useState(false);

  const getAverageScore = (rating: Rating): number | null => {
    const scores = [
      rating.location_score,
      rating.house_quality_score,
      rating.garden_score,
      rating.value_score
    ].filter(s => s !== null) as number[];
    
    if (scores.length === 0) return null;
    return scores.reduce((a, b) => a + b, 0) / scores.length;
  };

  const avgScore = rating ? getAverageScore(rating) : null;

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
          <h3 className="property-title">{property.title}</h3>
          <p className="property-location">
            {property.postcode} {property.city}<br />
            {property.neighbourhood}
          </p>
        </div>
        
        <div className="property-price">
          € {property.price.toLocaleString('nl-NL')} k.k.
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
          <div className="property-stat">
            <span className="stat-bullet">•</span>
            <span>{property.bedrooms} slaapkamers</span>
          </div>
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
          <a href={property.funda_url} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
            View on Funda
          </a>
          
          {!rating || rating.status === 'unreviewed' ? (
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