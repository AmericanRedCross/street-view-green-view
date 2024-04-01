## Imagery collection issues

### Mapillary fails to process videos >2GB 

Uploading raw GoPro `.360` video files fails during the processing phase. Mapillary support says videos >2GB presents issues.

- **Option 1:** Change collection settings.
    - Collect images rather than videos - 2s interval. Note that this may not be possible depending on travel speed during collection and imagery coverage requirements.
- **Option 2:** Preprocess the .360 video with GoPro software.
    - Download GoPro Player App [https://gopro.com/en/us/info/gopro-player](https://gopro.com/en/us/info/gopro-player).
    - Open large `.360` video file in GoPro Player app.
    - File `Export As...` -> `5.6K`, Export Settings window will open.
    - Expand the `Advanced Options` window.
    - Change Codec to `HEVC`.
    - Check the `Retain GPMF Data` Option (previously greyed out).
    - Click `Next`.
    - Select the save location and click `Save`.
    - File will export and will be a large, `.mp4` file.
