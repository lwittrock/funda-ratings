#!/usr/bin/env python3
"""
Funda Search Script with Supabase Integration
Reads search config from Supabase and saves results back
Now includes distance calculation to train stations AND coordinates
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from funda import Funda
from supabase import create_client, Client
from dotenv import load_dotenv
import requests
import time

# Load environment variables from .env file
load_dotenv()

# Load environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
    exit(1)

if not GOOGLE_MAPS_API_KEY:
    print("⚠️  Warning: GOOGLE_MAPS_API_KEY not set - distance calculations will be skipped")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Station mapping per city
STATION_MAP = {
    'breda': 'Breda Station, Netherlands',
    'etten-leur': 'Etten-Leur Station, Netherlands',
    'delft': 'Delft Station, Netherlands',
    'tilburg': 'Tilburg Station, Netherlands',
    'rijen': 'Station Gilzen-Rijen, Netherlands',
    'teteringen': 'Breda Station, Netherlands',
}


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


def get_station_for_city(city):
    """Get the train station address for a given city"""
    if not city:
        return None
    
    city_normalized = city.lower().strip()
    return STATION_MAP.get(city_normalized)


def calculate_distance_to_station(property_address, station_address, mode='walking'):
    """
    Calculate travel time to station using Google Maps Distance Matrix API
    
    Args:
        property_address: Full address of the property
        station_address: Address of the train station
        mode: 'walking', 'bicycling', or 'transit'
    
    Returns:
        int: Travel time in minutes, or 'N/A' if route not available
    """
    if not GOOGLE_MAPS_API_KEY:
        return None
    
    try:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            'origins': property_address,
            'destinations': station_address,
            'mode': mode,
            'key': GOOGLE_MAPS_API_KEY,
            'language': 'nl',
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check if we got valid results
        if data.get('status') != 'OK':
            print(f"      ⚠️  API status: {data.get('status')}")
            return 'N/A'
        
        rows = data.get('rows', [])
        if not rows or not rows[0].get('elements'):
            return 'N/A'
        
        element = rows[0]['elements'][0]
        
        # Check element status
        if element.get('status') != 'OK':
            # Route not available (e.g., no transit connection)
            return 'N/A'
        
        # Get duration in seconds and convert to minutes
        duration_seconds = element.get('duration', {}).get('value')
        if duration_seconds:
            return round(duration_seconds / 60)
        
        return 'N/A'
        
    except requests.exceptions.RequestException as e:
        print(f"      ⚠️  Request error for {mode}: {e}")
        return 'N/A'
    except Exception as e:
        print(f"      ⚠️  Error calculating {mode} distance: {e}")
        return 'N/A'


def calculate_all_distances(property_data):
    """
    Calculate walking, biking, and transit distances to nearest station
    Only calculates if distances are not already set
    
    Args:
        property_data: Dict with property information including city and address
    
    Returns:
        Dict with distance fields added/updated
    """
    # Skip if already calculated (not None and not empty)
    if (property_data.get('distance_station_walk') is not None or
        property_data.get('distance_station_bike') is not None or
        property_data.get('distance_station_transit') is not None):
        return property_data
    
    # Skip if no Google Maps API key
    if not GOOGLE_MAPS_API_KEY:
        return property_data
    
    city = property_data.get('city')
    station_address = get_station_for_city(city)
    
    if not station_address:
        # City not in our station map - skip
        return property_data
    
    # Build full property address
    parts = []
    if property_data.get('title'):
        parts.append(property_data['title'])
    if property_data.get('postcode'):
        parts.append(property_data['postcode'])
    if city:
        parts.append(city)
    
    property_address = ', '.join(parts)
    
    if not property_address:
        return property_data
    
    print(f"      🗺️  Calculating distances to {station_address}...")
    
    # Calculate each mode with small delay between requests
    walk_time = calculate_distance_to_station(property_address, station_address, 'walking')
    time.sleep(0.2)  # Small delay to avoid rate limiting
    
    bike_time = calculate_distance_to_station(property_address, station_address, 'bicycling')
    time.sleep(0.2)
    
    transit_time = calculate_distance_to_station(property_address, station_address, 'transit')
    
    # Store results
    property_data['nearest_station_name'] = station_address.split(',')[0]  # Just "Breda Station"
    property_data['distance_station_walk'] = walk_time
    property_data['distance_station_bike'] = bike_time
    property_data['distance_station_transit'] = transit_time
    
    print(f"      ✅ Walk: {walk_time}min | Bike: {bike_time}min | Transit: {transit_time}min")
    
    return property_data


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
        'funda_status': listing.get('status'),  # Funda's status (available/sold)
        
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
        'features_data': {},  # Can store additional data here if needed
        
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
    
    # Process each search configuration
    for idx, config in enumerate(search_configs, 1):
        city = config.get('city')
        neighborhoods = config.get('neighborhoods', [])
        price_min = config.get('price_min')
        price_max = config.get('price_max')
        area_min = config.get('area_min')
        max_results = config.get('max_results', 50)
        
        print(f"\n{'='*80}")
        print(f"🔍 Search Config #{idx}: {city.title()}")
        print(f"{'='*80}")
        
        if neighborhoods:
            print(f"   Neighborhoods: {', '.join([n.title() for n in neighborhoods])}")
        if price_min or price_max:
            print(f"   Price: €{price_min:,} - €{price_max:,}".replace(',', '.'))
        if area_min:
            print(f"   Min area: {area_min} m²")
        
        # Search
        print("\n🔧 Running search...")
        try:
            results = f.search_listing(
                location=city,
                price_min=price_min,
                price_max=price_max,
                area_min=area_min,
            )
        except Exception as e:
            print(f"   ❌ Search error: {e}")
            print("   Trying without area filter...")
            try:
                results = f.search_listing(
                    location=city,
                    price_min=price_min,
                    price_max=price_max,
                )
                if area_min:
                    results = [r for r in results if extract_int(r.get('living_area')) and extract_int(r.get('living_area')) >= area_min]
                    print(f"   After manual area filter: {len(results)} results")
            except Exception as e2:
                print(f"   ❌ Alternative search also failed: {e2}")
                continue
        
        print(f"   Found {len(results)} properties from API")
        
        # Filter by neighborhoods if specified
        if neighborhoods:
            normalized_neighborhoods = [normalize_name(n) for n in neighborhoods]
            filtered = []
            
            for listing in results:
                neighborhood = listing.get('neighbourhood', '')
                if neighborhood and normalize_name(neighborhood) in normalized_neighborhoods:
                    filtered.append(listing)
            
            results = filtered
            print(f"   After neighborhood filter: {len(results)} properties")
        
        # Limit results
        results = results[:max_results]
        
        # Process results
        new_count = 0
        updated_count = 0
        
        print(f"\n💾 Processing {len(results)} properties...")
        
        for prop_idx, listing in enumerate(results, 1):
            try:
                global_id = listing.get('global_id') or listing.get('tiny_id')
                
                if prop_idx == 1 or prop_idx % 10 == 0:
                    print(f"   [{prop_idx}/{len(results)}] Processing...")
                
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
                    print(f"      URL: {property_data['url']}")
                    if property_data['latitude'] and property_data['longitude']:
                        print(f"      Coordinates: {property_data['latitude']}, {property_data['longitude']}")
                
                if funda_id in existing_properties:
                    # Update existing - preserve user review data
                    old_data = existing_properties[funda_id]
                    property_data['review_status'] = old_data.get('review_status', 'new')
                    property_data['rating_location'] = old_data.get('rating_location')
                    property_data['rating_quality'] = old_data.get('rating_quality')
                    property_data['rating_outside'] = old_data.get('rating_outside')
                    property_data['rating_value'] = old_data.get('rating_value')
                    property_data['notes'] = old_data.get('notes')
                    property_data['id'] = old_data.get('id')  # Preserve DB id
                    
                    # Preserve distance data if already calculated
                    if old_data.get('distance_station_walk') is not None:
                        property_data['nearest_station_name'] = old_data.get('nearest_station_name')
                        property_data['distance_station_walk'] = old_data.get('distance_station_walk')
                        property_data['distance_station_bike'] = old_data.get('distance_station_bike')
                        property_data['distance_station_transit'] = old_data.get('distance_station_transit')
                    
                    updated_count += 1
                else:
                    # New property
                    new_count += 1
                
                # Calculate distances to station (only if not already set)
                property_data = calculate_all_distances(property_data)
                
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
    
    # Summary
    print("\n" + "="*80)
    print("✅ ALL SEARCHES COMPLETE")
    print("="*80)
    print(f"   🆕 Total new properties: {total_new}")
    print(f"   🔄 Total updated properties: {total_updated}")
    print(f"   📊 Total in database: {len(existing_properties) + total_new}")
    print(f"\n💾 Data saved to Supabase!")
    print(f"🌐 Your app will now load from the database\n")


if __name__ == "__main__":
    try:
        search_properties()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()