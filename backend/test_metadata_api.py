"""
Test script for Metadata Extraction API
Creates a test image with GPS coordinates and uploads it
"""

import io
import httpx
from PIL import Image
import piexif
from datetime import datetime


def create_test_image_with_gps():
    """Create a test JPEG image with GPS EXIF data"""
    # Create a simple test image
    img = Image.new('RGB', (800, 600), color='blue')
    
    # Prepare EXIF data with GPS coordinates
    # Example: Statue of Liberty coordinates
    latitude = 40.689247
    longitude = -74.044502
    
    def decimal_to_dms(decimal):
        """Convert decimal degrees to degrees, minutes, seconds"""
        degrees = int(decimal)
        minutes_decimal = abs(decimal - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60
        return ((degrees, 1), (minutes, 1), (int(seconds * 100), 100))
    
    # Convert coordinates
    lat_dms = decimal_to_dms(abs(latitude))
    lon_dms = decimal_to_dms(abs(longitude))
    
    lat_ref = 'N' if latitude >= 0 else 'S'
    lon_ref = 'E' if longitude >= 0 else 'W'
    
    # Build EXIF dictionary
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: b"Apple",
            piexif.ImageIFD.Model: b"iPhone 14 Pro",
            piexif.ImageIFD.Software: b"iOS 17.0",
            piexif.ImageIFD.DateTime: datetime.now().strftime("%Y:%m:%d %H:%M:%S").encode()
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: b"2024:11:15 14:30:00",
            piexif.ExifIFD.ISOSpeedRatings: 100,
            piexif.ExifIFD.FocalLength: (26, 1),
            piexif.ExifIFD.ExposureTime: (1, 125),
            piexif.ExifIFD.FNumber: (18, 10),  # f/1.8
        },
        "GPS": {
            piexif.GPSIFD.GPSLatitudeRef: lat_ref.encode(),
            piexif.GPSIFD.GPSLatitude: lat_dms,
            piexif.GPSIFD.GPSLongitudeRef: lon_ref.encode(),
            piexif.GPSIFD.GPSLongitude: lon_dms,
            piexif.GPSIFD.GPSAltitude: (10, 1),  # 10 meters
        }
    }
    
    # Convert to bytes
    exif_bytes = piexif.dump(exif_dict)
    
    # Save image with EXIF
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG', exif=exif_bytes, quality=95)
    img_io.seek(0)
    
    return img_io


async def test_metadata_extraction():
    """Test the metadata extraction API"""
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║         Metadata Extraction API - Test Suite                    ║")
    print("╚══════════════════════════════════════════════════════════════════╝\n")
    
    # Create test image
    print("📸 Creating test image with GPS metadata...")
    print("   Location: Statue of Liberty, New York")
    print("   Coordinates: 40.689247, -74.044502\n")
    
    image_data = create_test_image_with_gps()
    
    # Upload to API
    print("📤 Uploading image to metadata extraction API...\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        files = {'file': ('test_photo.jpg', image_data, 'image/jpeg')}
        
        try:
            response = await client.post(
                'http://localhost:8000/api/v1/metadata/extract',
                files=files
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print("✅ Extraction successful!\n")
                print(f"📄 Filename: {result['filename']}")
                print(f"📊 Size: {result['file_size_mb']} MB")
                print(f"🔤 Format: {result['file_extension']}\n")
                
                metadata = result.get('metadata', {})
                
                # Image info
                if metadata.get('size'):
                    print("🖼️  Image Information:")
                    print(f"   Format: {metadata['format']}")
                    print(f"   Dimensions: {metadata['size']['width']} × {metadata['size']['height']} px")
                    print(f"   Megapixels: {metadata['size']['megapixels']} MP\n")
                
                # Camera info
                if metadata.get('camera'):
                    print("📷 Camera Information:")
                    print(f"   Make: {metadata['camera']['make']}")
                    print(f"   Model: {metadata['camera']['model']}")
                    print(f"   Software: {metadata['camera']['software']}\n")
                
                # GPS location
                if result.get('triangulation', {}).get('available'):
                    print("📍 GPS LOCATION FOUND!")
                    location = result['triangulation']['location']
                    print(f"   Latitude: {location['latitude']:.6f}°")
                    print(f"   Longitude: {location['longitude']:.6f}°")
                    if location.get('altitude'):
                        print(f"   Altitude: {location['altitude']} m")
                    print(f"\n   🗺️  Google Maps URL:")
                    print(f"   {location['google_maps_url']}\n")
                    print(f"   💡 {result['triangulation']['suggestion']}\n")
                else:
                    print("⚠️  No GPS data found in image\n")
                
                print("="*68)
                print("✓ Test completed successfully!")
                print("="*68)
                
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Error during upload: {e}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(test_metadata_extraction())
