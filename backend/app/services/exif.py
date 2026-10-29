from typing import Optional, Tuple, Dict, Any
from PIL import Image, ExifTags
from app.core.logging import logger

def _get_exif_field(exif_dict: Dict[int, Any], tag_name: str) -> Optional[Any]:
    for tag_id, name in ExifTags.TAGS.items():
        if name == tag_name:
            return exif_dict.get(tag_id)
    return None

def _convert_dms_to_decimal(dms: Tuple, ref: str) -> Optional[float]:
    """Converts GPS degrees, minutes, seconds tuple to decimal degrees."""
    try:
        def to_float(val):
            if hasattr(val, "numerator") and hasattr(val, "denominator"):
                return float(val.numerator) / float(val.denominator) if val.denominator != 0 else 0.0
            return float(val)

        d = to_float(dms[0])
        m = to_float(dms[1])
        s = to_float(dms[2])
        dec = d + (m / 60.0) + (s / 3600.0)
        if ref.upper() in ["S", "W"]:
            dec = -dec
        return round(dec, 6)
    except Exception as e:
        logger.warning(f"Failed to convert DMS to decimal: {e}")
        return None

def extract_exif_metadata(image_path: str) -> Dict[str, Any]:
    """
    Extracts GPS latitude, longitude, and device metadata from EXIF tags.
    Returns:
        {
            "latitude": float or None,
            "longitude": float or None,
            "has_gps": bool,
            "camera_make": str or None,
            "camera_model": str or None,
            "date_taken": str or None
        }
    """
    result = {
        "latitude": None,
        "longitude": None,
        "has_gps": False,
        "camera_make": None,
        "camera_model": None,
        "date_taken": None
    }

    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if not exif_data:
                return result

            # Camera metadata
            result["camera_make"] = _get_exif_field(exif_data, "Make")
            result["camera_model"] = _get_exif_field(exif_data, "Model")
            result["date_taken"] = _get_exif_field(exif_data, "DateTimeOriginal") or _get_exif_field(exif_data, "DateTime")

            # GPS metadata
            gps_info_tag = None
            for tag_id, name in ExifTags.TAGS.items():
                if name == "GPSInfo":
                    gps_info_tag = tag_id
                    break

            if gps_info_tag and gps_info_tag in exif_data:
                gps_dict = exif_data[gps_info_tag]
                gps_tags = ExifTags.GPSTAGS

                lat_dms = None
                lat_ref = "N"
                lon_dms = None
                lon_ref = "E"

                for k, v in gps_dict.items():
                    tag_name = gps_tags.get(k)
                    if tag_name == "GPSLatitude":
                        lat_dms = v
                    elif tag_name == "GPSLatitudeRef":
                        lat_ref = str(v)
                    elif tag_name == "GPSLongitude":
                        lon_dms = v
                    elif tag_name == "GPSLongitudeRef":
                        lon_ref = str(v)

                if lat_dms and lon_dms:
                    lat_dec = _convert_dms_to_decimal(lat_dms, lat_ref)
                    lon_dec = _convert_dms_to_decimal(lon_dms, lon_ref)
                    if lat_dec is not None and lon_dec is not None:
                        result["latitude"] = lat_dec
                        result["longitude"] = lon_dec
                        result["has_gps"] = True
    except Exception as e:
        logger.warning(f"Error parsing EXIF metadata from {image_path}: {e}")

    return result
