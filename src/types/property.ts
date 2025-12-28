export interface Property {
  id: number;
  funda_id: string;
  url: string;
  title: string;
  address: string;
  city: string;
  price: number;
  area: number;
  energy_label: string | null;
  status: ReviewStatus;
  rating_location: number | null;
  rating_quality: number | null;
  rating_value: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  // Additional fields from scraper
  thumbnail_url?: string | null;
  neighbourhood?: string | null;
  postcode?: string | null;
  province?: string | null;
  plot_area?: number | null;
  bedrooms?: number | null;
  rooms?: number | null;
  construction_year?: number | null;
  object_type?: string | null;
  house_type?: string | null;
  features?: {
    has_garden?: boolean;
    has_balcony?: boolean;
    has_roof_terrace?: boolean;
    has_solar_panels?: boolean;
    has_heat_pump?: boolean;
    has_parking?: boolean;
  };
}

export type ReviewStatus = 
  | 'new'
  | 'reviewed'
  | 'interested'
  | 'rejected';

export interface SearchConfig {
  id: number;
  city: string;
  neighborhoods: string[];
  price_min: number;
  price_max: number;
  area_min: number;
  max_results: number;
  active: boolean;
  created_at: string;
}

export interface PropertiesData {
  [id: string]: Property;
}