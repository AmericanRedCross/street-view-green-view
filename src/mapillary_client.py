from os import getenv, getcwd
import logging
from pathlib import Path
from mapillary import interface as mly
from requests import get, RequestException


class MapillaryClient:
    def __init__(self, access_token: str, log_level: int = logging.INFO, basepath: str = getcwd()) -> None:
        self.access_token = access_token
        mly.set_access_token(access_token)
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.addHandler(logging.StreamHandler())
        self.log.setLevel(log_level)
        self.basepath = basepath

    def get_images_from_coordinates(self, latitude: float, longitude: float) -> list[Path]:
        self.log.info("%s.%s: %s, %s",
                      self.__class__.__name__,
                      self.get_images_from_coordinates.__name__,
                      latitude,
                      longitude)

        images = mly.get_image_close_to(latitude, longitude, image_type="pano").to_dict()
        image_ids = list(map(lambda img: img["properties"]["id"], images["features"]))

        self.log.info("%s.%s: got %s images close to %s, %s",
                      self.__class__.__name__,
                      self.get_images_from_coordinates.__name__,
                      len(image_ids),
                      latitude,
                      longitude)
        self.log.debug(image_ids)

        return list(map(lambda img: self.download_image(img), image_ids))

    def download_image(self, image_id: int) -> Path:
        self.log.info("%s.%s: %s",
                      self.__class__.__name__,
                      self.download_image.__name__,
                      image_id)
        filepath = Path(self.basepath, f"{image_id}.jpg")
        image_url = mly.image_thumbnail(str(image_id), 2048)
        self.log.debug("%s.%s: image url for %s is %s",
                      self.__class__.__name__,
                      self.download_image.__name__,
                      image_id,
                      image_url)

        try:
            image_content = get(image_url).content
            with open(filepath, "wb") as image_file:
                image_file.write(image_content)
            self.log.debug("%s.%s: image %s downloaded to %s",
                          self.__class__.__name__,
                          self.download_image.__name__,
                          image_id,
                          filepath)
        except RequestException as e:
            self.log.error(e)

        return filepath


if __name__ == "__main__":
    client = MapillaryClient(getenv("MAPILLARY_API_KEY"))
    downloaded_images = client.get_images_from_coordinates(47.617663, -122.169819)
    logging.info(downloaded_images)
