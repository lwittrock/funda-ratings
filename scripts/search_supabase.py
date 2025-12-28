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

# Load environment variables from .env file
load_dotenv()

# Load environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
    exit(1)

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


def extract_property_data(listing):
    """Extract relevant data from Funda listing"""
    # Get photo URLs
    photo_urls = listing.get('photo_urls', [])
    if not photo_urls:
        photos = listing.get('photos', [])
        if photos and isinstance(photos, list):
            photo_urls = photos
    
    thumbnail_url = photo_urls[0] if photo_urls else None
    
    # Get URL
    funda_url = listing.get('url') or listing.get('share_url') or listing.get('funda_url')
    
    # Construct URL if not found
    if not funda_url:
        object_type = listing.get('object_type', 'huis').lower()
        if object_type == 'house':
            object_type = 'huis'
        elif object_type == 'apartment':
            object_type = 'appartement'
        
        city = listing.get('city', '').lower()
        title_slug = listing.get('title', '').lower().replace(' ', '-')
        property_id = listing.get('global_id') or listing.get('tiny_id')
        
        funda_url = f"https://www.funda.nl/detail/koop/{city}/{object_type}-{title_slug}/{property_id}/"
    
    # Get the ID
    funda_id = str(listing.get('global_id') or listing.get('tiny_id'))
    
    # Build address
    title = listing.get('title', '')
    postcode = listing.get('postcode', '')
    city = listing.get('city', '')
    address = f"{title}, {postcode} {city}".strip(', ')
    
    return {
        'funda_id': funda_id,
        'url': funda_url,
        'title': title,
        'address': address,
        'city': city,
        'price': extract_int(listing.get('price')),
        'area': extract_int(listing.get('living_area')),
        'energy_label': listing.get('energy_label'),
        'status': 'new',  # Default status for new properties
        'thumbnail_url': thumbnail_url,
        'neighbourhood': listing.get('neighbourhood'),
        'postcode': postcode,
        'province': listing.get('province'),
        'plot_area': extract_int(listing.get('plot_area')),
        'bedrooms': extract_int(listing.get('bedrooms')),
        'rooms': extract_int(listing.get('rooms')),
        'construction_year': extract_int(listing.get('construction_year')),
        'object_type': listing.get('object_type'),
        'house_type': listing.get('house_type'),
        'features': {
            'has_garden': listing.get('has_garden', False),
            'has_balcony': listing.get('has_balcony', False),
            'has_roof_terrace': listing.get('has_roof_terrace', False),
            'has_solar_panels': listing.get('has_solar_panels', False),
            'has_heat_pump': listing.get('has_heat_pump', False),
            'has_parking': listing.get('has_parking_on_site', False),
        },
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
                
                if funda_id in existing_properties:
                    # Update existing - preserve user ratings and status
                    old_data = existing_properties[funda_id]
                    property_data['status'] = old_data.get('status', 'new')
                    property_data['rating_location'] = old_data.get('rating_location')
                    property_data['rating_quality'] = old_data.get('rating_quality')
                    property_data['rating_value'] = old_data.get('rating_value')
                    property_data['notes'] = old_data.get('notes')
                    property_data['id'] = old_data.get('id')  # Preserve DB id
                    updated_count += 1
                else:
                    # New property
                    new_count += 1
                
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