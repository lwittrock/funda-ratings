export interface Property {
  id: string;
  title: string;
  city: string;
  neighbourhood: string;
  postcode: string;
  province: string;
  price: number;
  living_area: number;
  plot_area: number | null;
  bedrooms: number;
  rooms: number;
  construction_year: number | null;
  energy_label: string | null;
  object_type: string;
  house_type: string | null;
  features: {
    has_garden: boolean;
    has_balcony: boolean;
    has_roof_terrace: boolean;
    has_solar_panels: boolean;
    has_heat_pump: boolean;
    has_parking: boolean;
  };
  thumbnail_url: string | null;
  funda_url: string;
  added_date: string;
  last_seen: string;
  status: 'active' | 'removed';
  removed_date?: string;
  price_history: Array<{
    price: number;
    date: string;
  }>;
}

export type ReviewStatus = 
  | 'unreviewed'
  | 'rejected'
  | 'reviewed'
  | 'viewing_interest';

export interface Rating {
  property_id: string;
  status: ReviewStatus;
  location_score: number | null;
  house_quality_score: number | null;
  garden_score: number | null;
  value_score: number | null;
  notes: string;
  rejection_reason: string | null;
  reviewed_date: string;
  updated_date: string;
}

export interface PropertiesData {
  [id: string]: Property;
}

export interface RatingsData {
  [id: string]: Rating;
}