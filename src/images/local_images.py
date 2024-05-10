from pathlib import Path

from geopy import Point
from geopy.distance import ELLIPSOIDS, distance
import numpy as np
from PIL.ExifTags import GPS
from PIL.Image import open

from src.images.image_source import ImageSource
from src.utils import log

EXIF_GPS_TAG = 34853


class LocalImages(ImageSource):
    def __init__(self, basepath: Path) -> None:
        super().__init__(basepath)
        dir_images = (
            set().union(basepath.glob("**/*.jpg")).union(basepath.glob("**/*.jpeg"))
        )
        if len(dir_images) == 0:
            raise FileNotFoundError(f"No Images Found In Path: {basepath}")

        self.images = dict()
        for image_path in dir_images:
            with open(image_path) as image:
                exif_data = image._getexif()
                gps_data = exif_data.get(EXIF_GPS_TAG)

                latitude_dms = gps_data[GPS.GPSLatitude]
                latitude_dir = gps_data[GPS.GPSLatitudeRef]
                longitude_dms = gps_data[GPS.GPSLongitude]
                longitude_dir = gps_data[GPS.GPSLongitudeRef]

                location = "{} {}m {}s {} {} {}m {}s {}".format(
                    latitude_dms[0],
                    latitude_dms[1],
                    latitude_dms[2],
                    latitude_dir,
                    longitude_dms[0],
                    longitude_dms[1],
                    longitude_dms[2],
                    longitude_dir,
                )

                self.images[location] = image_path

        self.assigned_images = set()

        log.debug("Images in Directory: %s", self.images)

    def get_image_from_coordinates(self, latitude: int, longitude: int) -> dict:
        log.debug("Get Image From Coordinates: %s, %s", latitude, longitude)
        results = {
            "image_lat": None,
            "image_lon": None,
            "residual": None,
            "image_id": None,
            "image_path": None,
            "error": None,
        }

        filtered_images = set(
            filter(
                lambda image_point: image_point not in self.assigned_images, self.images
            )
        )
        if len(filtered_images) == 0:
            log.debug("No Unassigned Images Available")
            return results

        closest = None
        closest_distance = np.inf
        for p, point in enumerate(filtered_images):
            image_coordinates = Point(point)
            coordinates = Point(latitude, longitude)
            residual = distance(
                coordinates, image_coordinates, ellipsoid=ELLIPSOIDS["WGS-84"]
            )

            if residual < closest_distance:
                closest = point
                closest_distance = residual

        image = self.images[closest]
        log.debug("Closest Image: %s", image)
        results["image_id"] = image.stem
        image_coordinates = Point(closest)
        results["image_lat"] = image_coordinates.latitude
        results["image_lon"] = image_coordinates.longitude
        results["residual"] = closest_distance.m
        results["image_path"] = image
        self.assigned_images.add(closest)

        return results
