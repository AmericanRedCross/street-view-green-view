from pathlib import Path

from geopy import Point
from geopy.distance import ELLIPSOIDS, distance
from loguru import logger as log
import numpy as np
from PIL.ExifTags import GPS
from PIL.Image import open
from typing_extensions import override

from src.images.image_source import ImageSource

EXIF_GPS_TAG = 34853


class LocalImages(ImageSource):
    def __init__(self, images_path: Path) -> None:
        """
        All Args Constructor
        :param images_path: Where the Images Should Be Located
        """
        super().__init__(images_path)
        dir_images = (
            set()
            .union(images_path.glob("**/*.jpg"))
            .union(images_path.glob("**/*.jpeg"))
        )
        if len(dir_images) == 0:
            raise FileNotFoundError(f"No Images Found In Path: {images_path}")

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

                self.images[image_path] = location

        self.assigned_images = set()

        log.debug("Images in Directory: {}", self.images)

    @override
    def get_image_from_coordinates(self, latitude: float, longitude: float) -> dict:
        """
        Gets an Image for a Set of Coordinates
        From A Folder of Local Images Using EXIF Data
        :param latitude: Latitude of the Point to Get an Image for
        :param longitude: Longitude of the Point to Get an Image for
        :return: A Dictionary Containing the Image ID, Path, Latitude, Longitude,
        Residual Distance From Point, and Error if any
        """
        log.debug("Get Image From Coordinates: {}, {}", latitude, longitude)
        results = {
            "image_lat": None,
            "image_lon": None,
            "residual": None,
            "image_id": None,
            "image_path": None,
            "error": None,
        }

        filtered_images = filter(
            lambda img: img not in self.assigned_images, self.images.keys()
        )

        closest = None
        closest_distance = np.inf
        for i, image in enumerate(filtered_images):
            image_coordinates = Point(self.images[image])
            coordinates = Point(latitude, longitude)
            residual = distance(
                coordinates, image_coordinates, ellipsoid=ELLIPSOIDS["WGS-84"]
            )

            if residual < closest_distance:
                closest = image
                closest_distance = residual

        if closest is None and closest_distance == np.inf:
            log.debug("No Unassigned Images Available")
            return results

        image = closest
        log.debug("Closest Image: {}", image)
        results["image_id"] = image.stem
        image_coordinates = Point(self.images[image])
        results["image_lat"] = image_coordinates.latitude
        results["image_lon"] = image_coordinates.longitude
        results["residual"] = closest_distance.m
        results["image_path"] = image.resolve()
        self.assigned_images.add(image)

        return results
