#!/usr/bin/env python3
"""
Funda Search Script with Supabase Integration
Reads search config from Supabase and saves results back
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from funda import Funda
from supabase import create_client, Client
from dotenv import load_dotenv

# Import our modules
from station_config import get_station_for_city
from distance_calculator import calculate_all_distances, estimate_api_calls, GOOGLE_MAPS_API_KEY

# Load environment variables from .env file
load_dotenv()

# Load environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
    exit(1)

if not GOOGLE_MAPS_API_KEY:
    print("⚠️  Warning: GOOGLE_MAPS_API_KEY not set - distance calculations will be skipped")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def load_search_configs():
    """Load active search configurations from Supabase"""
    try:
        response = supabase.table('search_configs').select('*').eq('active', True).execute()
        return response.data
    except Exception as e:
        print(f"❌ Error loading search configs: {e}")
        return []


def load_existing_properties():
    """Load existing properties from Supabase"""
    try:
        response = supabase.table('properties').select('*').execute()
        # Convert list to dict keyed by funda_id
        return {prop['funda_id']: prop for prop in response.data}
    except Exception as e:
        print(f"⚠️  Warning: Could not load existing properties: {e}")
        return {}


def upsert_property(property_data):
    """Insert or update a property in Supabase"""
    try:
        # Use funda_id for upsert conflict resolution
        supabase.table('properties').upsert(property_data, on_conflict='funda_id').execute()
    except Exception as e:
        print(f"   ❌ Failed to upsert property {property_data.get('funda_id')}: {e}")
        raise


def normalize_name(name):
    """Normalize names for comparison"""
    return name.lower().replace(' ', '').replace('-', '')


def extract_int(value):
    """Extract integer from string like '148 m²' or return int/None"""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = re.search(r'\d+', value)
        return int(match.group()) if match else None
    return None


def extract_coordinates(listing):
    """Extract latitude and longitude from listing"""
    # Try to get coordinates tuple
    coords = listing.get('coordinates')
    if coords and isinstance(coords, (list, tuple)) and len(coords) == 2:
        return float(coords[0]), float(coords[1])
    
    # Try individual fields
    lat = listing.get('latitude')
    lng = listing.get('longitude')
    
    if lat is not None and lng is not None:
        try:
            return float(lat), float(lng)
        except (ValueError, TypeError):
            pass
    
    return None, None


def extract_property_data(listing):
    """Extract ALL data from Funda listing and map to database schema"""
    
    # Get photo URLs
    photo_urls = listing.get('photo_urls', [])
    if not photo_urls:
        photos = listing.get('photos', [])
        if photos and isinstance(photos, list):
            photo_urls = photos
    
    thumbnail_url = photo_urls[0] if photo_urls else None
    
    # Get URL
    funda_url = listing.get('url') or listing.get('share_url')
    
    # Construct URL if not found
    if not funda_url:
        object_type_slug = listing.get('object_type', 'huis').lower()
        if object_type_slug == 'house':
            object_type_slug = 'huis'
        elif object_type_slug == 'apartment':
            object_type_slug = 'appartement'
        
        city = listing.get('city', '').lower()
        title_slug = listing.get('title', '').lower().replace(' ', '-')
        property_id = listing.get('global_id') or listing.get('tiny_id')
        
        funda_url = f"https://www.funda.nl/detail/koop/{city}/{object_type_slug}-{title_slug}/{property_id}/"
    
    # Extract coordinates
    latitude, longitude = extract_coordinates(listing)
    
    # Extract all fields matching the database schema
    return {
        # Identifiers
        'funda_id': str(listing.get('global_id') or listing.get('tiny_id')),
        'tiny_id': str(listing.get('tiny_id')) if listing.get('tiny_id') else None,
        
        # Address
        'title': listing.get('title'),
        'city': listing.get('city'),
        'postcode': listing.get('postcode'),
        'province': listing.get('province'),
        'neighbourhood': listing.get('neighbourhood'),
        'municipality': listing.get('municipality'),
        'house_number': listing.get('house_number'),
        'house_number_ext': listing.get('house_number_ext'),
        
        # Coordinates
        'latitude': latitude,
        'longitude': longitude,
        
        # Price
        'price': extract_int(listing.get('price')),
        'price_formatted': listing.get('price_formatted'),
        
        # Property details
        'offering_type': listing.get('offering_type'),
        'object_type': listing.get('object_type'),
        'construction_type': listing.get('construction_type'),
        'house_type': listing.get('house_type'),
        'funda_status': listing.get('status'),
        
        # Measurements
        'living_area': extract_int(listing.get('living_area')),
        'plot_area': extract_int(listing.get('plot_area')),
        'bedrooms': extract_int(listing.get('bedrooms')),
        'rooms': extract_int(listing.get('rooms')),
        'construction_year': extract_int(listing.get('construction_year')),
        
        # Energy & Features
        'energy_label': listing.get('energy_label'),
        'has_garden': listing.get('has_garden', False),
        'has_balcony': listing.get('has_balcony', False),
        'has_solar_panels': listing.get('has_solar_panels', False),
        'has_heat_pump': listing.get('has_heat_pump', False),
        'has_roof_terrace': listing.get('has_roof_terrace', False),
        'has_parking_on_site': listing.get('has_parking_on_site', False),
        'has_parking_enclosed': listing.get('has_parking_enclosed', False),
        'is_energy_efficient': listing.get('is_energy_efficient', False),
        'is_monument': listing.get('is_monument', False),
        'is_fixer_upper': listing.get('is_fixer_upper', False),
        
        # Listing details
        'description': listing.get('description'),
        'highlight': listing.get('highlight'),
        'publication_date': listing.get('publication_date'),
        'open_house': listing.get('open_house', False),
        'is_auction': listing.get('is_auction', False),
        
        # URLs
        'url': funda_url,
        'share_url': listing.get('share_url'),
        'google_maps_url': listing.get('google_maps_url'),
        'brochure_url': listing.get('brochure_url'),
        'thumbnail_url': thumbnail_url,
        
        # Media (as JSON)
        'photos': photo_urls,
        'features_data': {},
        
        # Review fields (default for new properties)
        'review_status': 'new',
        'rating_location': None,
        'rating_quality': None,
        'rating_outside': None,
        'rating_value': None,
        'notes': None,
        
        # Distance fields (will be calculated separately)
        'nearest_station_name': None,
        'distance_station_walk': None,
        'distance_station_bike': None,
        'distance_station_transit': None,
    }


def parse_cities(city_input):
    """
    Parse city input - can be single city or comma-separated list
    
    Args:
        city_input: String like "breda" or "breda, tilburg, delft"
        
    Returns:
        List of city names
    """
    if not city_input:
        return []
    
    if isinstance(city_input, list):
        return city_input
    
    # Split by comma and clean up
    cities = [c.strip().lower() for c in city_input.split(',')]
    return [c for c in cities if c]  # Remove empty strings


def apply_config_filters(results, config):
    """
    Apply search config filters to results
    Filters for: neighborhoods, has_garden, has_parking
    (Distance filtering happens after distance calculation)
    
    Args:
        results: List of property listings
        config: Search config dict
        
    Returns:
        Filtered list of properties
    """
    filtered = []
    
    neighborhoods = config.get('neighborhoods', [])
    require_garden = config.get('require_garden', False)
    require_parking = config.get('require_parking', False)
    
    for listing in results:
        # Neighborhood filter
        if neighborhoods:
            neighborhood = listing.get('neighbourhood', '')
            normalized_neighborhoods = [normalize_name(n) for n in neighborhoods]
            if not neighborhood or normalize_name(neighborhood) not in normalized_neighborhoods:
                continue
        
        # Garden filter
        if require_garden and not listing.get('has_garden', False):
            continue
        
        # Parking filter
        if require_parking and not listing.get('has_parking_on_site', False):
            continue
        
        filtered.append(listing)
    
    return filtered


def passes_distance_filter_from_config(property_data, config):
    """
    Check if property passes the distance filter specified in the config
    
    Args:
        property_data: Property dict with distance fields
        config: Search config with max_distance_mode and max_distance_minutes
        
    Returns:
        True if property passes filter (or no filter specified)
    """
    mode = config.get('max_distance_mode')
    max_minutes = config.get('max_distance_minutes')
    
    # No filter specified
    if not mode or max_minutes is None:
        return True
    
    # Get the distance for the specified mode
    distance_key = f'distance_station_{mode}'
    distance = property_data.get(distance_key)
    
    # If distance not calculated yet, accept it (benefit of the doubt)
    if distance is None or distance == 'N/A':
        return True
    
    # Check if it exceeds the max
    if isinstance(distance, (int, float)) and distance > max_minutes:
        return False
    
    return True


def search_properties():
    """Main search function"""
    print("="*80)
    print("🏠 FUNDA PROPERTY SEARCH (Supabase)")
    print("="*80)
    
    # Load search configurations from Supabase
    print("\n📋 Loading search configurations from Supabase...")
    search_configs = load_search_configs()
    
    if not search_configs:
        print("❌ No active search configurations found in Supabase!")
        print("   Add a search config in your Supabase dashboard.")
        return
    
    print(f"   Found {len(search_configs)} active search configuration(s)")
    
    # Load existing properties
    print("\n📊 Loading existing properties from Supabase...")
    existing_properties = load_existing_properties()
    print(f"   Currently tracking {len(existing_properties)} properties")
    
    # Initialize Funda API
    f = Funda()
    
    total_new = 0
    total_updated = 0
    total_rejected_filter = 0
    new_properties_count = 0  # For API cost estimation
    
    # Process each search configuration
    for idx, config in enumerate(search_configs, 1):
        city_input = config.get('city')
        cities = parse_cities(city_input)
        
        neighborhoods = config.get('neighborhoods', [])
        price_min = config.get('price_min')
        price_max = config.get('price_max')
        area_min = config.get('area_min')
        max_results = config.get('max_results', 50)
        require_garden = config.get('require_garden', False)
        require_parking = config.get('require_parking', False)
        distance_mode = config.get('max_distance_mode')
        distance_max = config.get('max_distance_minutes')
        
        print(f"\n{'='*80}")
        print(f"🔍 Search Config #{idx}: {', '.join([c.title() for c in cities])}")
        print(f"{'='*80}")
        
        if neighborhoods:
            print(f"   Neighborhoods: {', '.join([n.title() for n in neighborhoods])}")
        if price_min or price_max:
            print(f"   Price: €{price_min:,} - €{price_max:,}".replace(',', '.'))
        if area_min:
            print(f"   Min area: {area_min} m²")
        if require_garden:
            print(f"   Required: Garden")
        if require_parking:
            print(f"   Required: Parking")
        if distance_mode and distance_max:
            print(f"   Max distance: {distance_max}min by {distance_mode}")
        
        # Search each city
        all_results = []
        
        for city in cities:
            print(f"\n🔧 Searching {city.title()}...")
            try:
                results = f.search_listing(
                    location=city,
                    price_min=price_min,
                    price_max=price_max,
                    area_min=area_min,
                )
                print(f"   Found {len(results)} properties in {city.title()}")
                all_results.extend(results)
            except Exception as e:
                print(f"   ❌ Search error for {city}: {e}")
                continue
        
        print(f"\n   Total from all cities: {len(all_results)} properties")
        
        # Apply filters
        filtered = apply_config_filters(all_results, config)
        
        if len(filtered) < len(all_results):
            rejected = len(all_results) - len(filtered)
            print(f"   After filters: {len(filtered)} properties ({rejected} filtered out)")
            total_rejected_filter += rejected
        
        # Limit results
        filtered = filtered[:max_results]
        
        # Process results
        new_count = 0
        updated_count = 0
        skipped_distance = 0
        
        print(f"\n💾 Processing {len(filtered)} properties...")
        
        for prop_idx, listing in enumerate(filtered, 1):
            try:
                global_id = listing.get('global_id') or listing.get('tiny_id')
                
                if prop_idx == 1 or prop_idx % 10 == 0:
                    print(f"   [{prop_idx}/{len(filtered)}] Processing...")
                
                # Get detailed listing
                try:
                    detailed_listing = f.get_listing(global_id)
                    property_data = extract_property_data(detailed_listing)
                except Exception as e:
                    property_data = extract_property_data(listing)
                
                funda_id = property_data['funda_id']
                
                # Debug first property
                if prop_idx == 1:
                    print(f"\n   ✅ Sample property:")
                    print(f"      Title: {property_data['title']}")
                    print(f"      City: {property_data['city']}")
                    print(f"      Garden: {property_data['has_garden']}")
                    print(f"      URL: {property_data['url']}")
                
                is_new = funda_id not in existing_properties
                
                if is_new:
                    new_count += 1
                    new_properties_count += 1
                else:
                    # Update existing - preserve user review data
                    old_data = existing_properties[funda_id]
                    property_data['review_status'] = old_data.get('review_status', 'new')
                    property_data['rating_location'] = old_data.get('rating_location')
                    property_data['rating_quality'] = old_data.get('rating_quality')
                    property_data['rating_outside'] = old_data.get('rating_outside')
                    property_data['rating_value'] = old_data.get('rating_value')
                    property_data['notes'] = old_data.get('notes')
                    property_data['id'] = old_data.get('id')
                    
                    # Preserve distance data if already calculated
                    if old_data.get('distance_station_walk') is not None:
                        property_data['nearest_station_name'] = old_data.get('nearest_station_name')
                        property_data['distance_station_walk'] = old_data.get('distance_station_walk')
                        property_data['distance_station_bike'] = old_data.get('distance_station_bike')
                        property_data['distance_station_transit'] = old_data.get('distance_station_transit')
                    
                    updated_count += 1
                
                # Calculate distances (only if not already set)
                if GOOGLE_MAPS_API_KEY:
                    property_data = calculate_all_distances(property_data)
                else:
                    skipped_distance += 1
                
                # Check if passes distance filter from config (only for new properties)
                if is_new and not passes_distance_filter_from_config(property_data, config):
                    mode = config.get('max_distance_mode')
                    max_min = config.get('max_distance_minutes')
                    actual = property_data.get(f'distance_station_{mode}')
                    print(f"      ⏭️  Skipped: {actual}min by {mode} exceeds max {max_min}min")
                    total_rejected_filter += 1
                    continue
                
                # Upsert to Supabase
                upsert_property(property_data)
                
            except Exception as e:
                print(f"      ❌ Error processing property: {e}")
                continue
        
        total_new += new_count
        total_updated += updated_count
        
        print(f"\n   ✅ Config #{idx} complete:")
        print(f"      🆕 New: {new_count}")
        print(f"      🔄 Updated: {updated_count}")
        if skipped_distance > 0:
            print(f"      ⏭️  Skipped distance calc: {skipped_distance} (no API key)")
    
    # Summary
    print("\n" + "="*80)
    print("✅ ALL SEARCHES COMPLETE")
    print("="*80)
    print(f"   🆕 Total new properties: {total_new}")
    print(f"   🔄 Total updated properties: {total_updated}")
    print(f"   🚫 Total filtered out: {total_rejected_filter}")
    print(f"   📊 Total in database: {len(existing_properties) + total_new}")
    
    # API cost estimation
    if GOOGLE_MAPS_API_KEY and new_properties_count > 0:
        print("\n📊 Google Maps API Usage Estimate:")
        estimates = estimate_api_calls(new_properties_count)
        print(f"   Calls this run: ~{estimates['calls_per_run']}")
        print(f"   Est. monthly calls: ~{estimates['calls_per_month']} (if run daily)")
        if estimates['within_free_tier']:
            print(f"   ✅ Within free tier (40,000/month)")
        else:
            print(f"   ⚠️  Exceeds free tier - Est. cost: ${estimates['estimated_monthly_cost']:.2f}/month")
    
    print(f"\n💾 Data saved to Supabase!")
    print(f"🌐 Your app will now load from the database\n")


if __name__ == "__main__":
    try:
        search_properties()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()