export interface Property {
  // Database fields
  id: number;
  created_at: string;
  updated_at: string;
  
  // Review fields (YOUR data, not from Funda)
  review_status: ReviewStatus;
  rating_location: number | null;
  rating_quality: number | null;
  rating_outside: number | null;
  rating_value: number | null;
  notes: string | null;
  
  // Identifiers (from pyfunda)
  funda_id: string;
  tiny_id: string | null;
  
  // Address (from pyfunda)
  title: string;
  city: string;
  postcode: string | null;
  province: string | null;
  neighbourhood: string | null;
  municipality: string | null;
  house_number: string | null;
  house_number_ext: string | null;
  
  // Price (from pyfunda)
  price: number;
  price_formatted: string | null;
  
  // Property Details (from pyfunda)
  offering_type: string | null;
  object_type: string | null;
  construction_type: string | null;
  house_type: string | null;
  funda_status: string | null; // "available" or "sold" from Funda
  
  // Measurements (from pyfunda)
  living_area: number;
  plot_area: number | null;
  bedrooms: number | null;
  rooms: number | null;
  construction_year: number | null;
  
  // Energy & Features (from pyfunda)
  energy_label: string | null;
  has_garden: boolean;
  has_balcony: boolean;
  has_solar_panels: boolean;
  has_heat_pump: boolean;
  has_roof_terrace: boolean;
  has_parking_on_site: boolean;
  has_parking_enclosed: boolean;
  is_energy_efficient: boolean;
  is_monument: boolean;
  is_fixer_upper: boolean;
  
  // Listing Details (from pyfunda)
  description: string | null;
  highlight: string | null;
  publication_date: string | null;
  open_house: boolean;
  is_auction: boolean;

  // Location (from pyfunda)
  latitude?: number | null;
  longitude?: number | null;
  
  // URLs (from pyfunda)
  url: string;
  share_url: string | null;
  google_maps_url: string | null;
  brochure_url: string | null;
  thumbnail_url: string | null;
  
  // Media (stored as JSON)
  photos: string[];
  features_data: Record<string, any>;
  
  // Distance to train station (calculated via Google Maps)
  nearest_station_name: string | null;
  distance_station_walk: number | string | null; // minutes or 'N/A'
  distance_station_bike: number | string | null; // minutes or 'N/A'
  distance_station_transit: number | string | null; // minutes or 'N/A'
}

export type ReviewStatus = 
  | 'new'
  | 'reviewed'
  | 'interested'
  | 'rejected';

export interface SearchConfig {
  id: number;
  city: string; // Can be comma-separated: "breda, tilburg"
  neighborhoods: string[];
  price_min: number;
  price_max: number;
  area_min: number;
  max_results: number;
  require_garden: boolean;
  require_parking: boolean;
  max_distance_mode: 'walk' | 'bike' | 'transit' | null; // NEW
  max_distance_minutes: number | null; // NEW
  active: boolean;
  created_at: string;
}

export interface PropertiesData {
  [id: string]: Property;
}