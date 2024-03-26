"""Assign Green View score to point features

"""
import pandas as pd
import geopandas as gpd 
import os
from get_gvi_score import *


def assign_gvi_to_points(image_directory, interim_data, output_directory):
	"""

	Args: 
		image_directory: directory path for folder holding Mapillary images
		interim_data: file holding interim data (output from create_points.py)
		output_file: directory path to save GeoPackage output to 

	Returns: 
		GeoPackage containing a `gvi_scores` point layer

	"""
	# Check image directory exists
	if os.path.exists(image_directory): 
		pass
	else: 
		raise ValueError(
			"Image directory could not be found")
	# Check image directory contains image files 
	# (This is based on the jpeg export in download_images.py)
	if '.jpeg' in '\t'.join(os.listdir(os.path.join(image_directory))): 
		pass
	else:
		raise Exception(
			"Image directory doesn't contain expected contents (.jpeg files)")
	# Check interim data is valid
	# Point data
	if 'Point' in gpd.read_file(interim_data).geometry.type.unique(): 
		pass
	else: 
		raise Exception(
			"Expected point data in interim data file but none found")

	# Check output directory exists
	if os.path.exists(output_directory): 
			pass
	else: 
			raise ValueError(
				"Output directory could not be found")


	# Make an empty dataframe to hold the data
	df = pd.DataFrame({"filename": [], "gvi_score": []})

	# Loop through each image in the Mapillary folder and get the GVI score 
	for i in os.listdir(image_directory): 
		gvi_score = get_gvi_score(os.path.join(image_directory, i))

		temp_df = pd.DataFrame({"filename": [i], "gvi_score": [gvi_score]})

		print(i, "\t", str(gvi_score))

		df = pd.concat([df, temp_df], ignore_index=True)

	# Create an image ID from the file name, to match to the point dataset
	df['image_id'] = df['filename'].str[:-5]

	# Open the interim point data
	gdf = gpd.read_file(interim_data) 

	# Join the GVI score to the interim point data using the `image id` attribute
	gdf = gdf.merge(df, how='left', on='image_id')

	# Print how many records were matched on each side 

	# Export as GPKG
	gdf.to_file(os.path.join(output_directory, "image_points_with_gvi.gpkg"), layer="gvi_scores")
