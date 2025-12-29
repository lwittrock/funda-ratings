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
      property.rating_outside,
      property.rating_value
    ].filter(s => s !== null) as number[];
    
    if (scores.length === 0) return null;
    return scores.reduce((a, b) => a + b, 0) / scores.length;
  };

  const formatDistance = (value: number | string | null): string => {
    if (value === null || value === undefined) return '—';
    if (value === 'N/A') return 'N/A';
    return `${value}`;
  };

  // Build location line
  const buildLocationLine = (): string => {
    const parts = [];
    if (property.distance_station_walk || property.distance_station_bike || property.distance_station_transit) {
      parts.push(`🚶 ${formatDistance(property.distance_station_walk)}min`);
      parts.push(`🚴 ${formatDistance(property.distance_station_bike)}min`);
      parts.push(`🚌 ${formatDistance(property.distance_station_transit)}min`);
    }
    return parts.join(' · ');
  };

  // Build house line
  const buildHouseLine = (): string => {
    const parts = [];
    parts.push(`${property.living_area} m² wonen`);
    if (property.bedrooms) parts.push(`${property.bedrooms} slaapkamers`);
    if (property.energy_label) parts.push(`Energielabel ${property.energy_label}`);
    if (property.construction_year) parts.push(`Bouwjaar ${property.construction_year}`);
    return parts.join(', ');
  };

  // Build outside line
  const buildOutsideLine = (): string => {
    const parts = [];
    if (property.plot_area) parts.push(`${property.plot_area} m² perceel`);
    if (property.has_garden) parts.push('Tuin');
    if (property.has_parking_on_site) parts.push('Parkeren');
    return parts.join(', ');
  };

  const locationLine = buildLocationLine();
  const houseLine = buildHouseLine();
  const outsideLine = buildOutsideLine();
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
          {/* Locatie */}
          {locationLine && (
            <div className="property-stat">
              <span className="stat-bullet">•</span>
              <span><strong>Locatie:</strong> {locationLine}</span>
            </div>
          )}
          
          {/* Huis */}
          <div className="property-stat">
            <span className="stat-bullet">•</span>
            <span><strong>Huis:</strong> {houseLine}</span>
          </div>
          
          {/* Outside */}
          {outsideLine && (
            <div className="property-stat">
              <span className="stat-bullet">•</span>
              <span><strong>Outside:</strong> {outsideLine}</span>
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