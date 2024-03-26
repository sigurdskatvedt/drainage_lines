import os
from qgis.core import QgsProcessingFeedback, QgsVectorLayer
import processing
from dual_logger import log  # Ensure dual_logger.py is accessible from this script
import logging


class RasterOperations:
    def __init__(self, raster_folder, vector_layer_path, clipped_rasters_folder, mosaic_output_path):
        self.raster_folder = raster_folder
        self.vector_layer_path = vector_layer_path
        self.clipped_rasters_folder = clipped_rasters_folder
        self.mosaic_output_path = mosaic_output_path
        self.feedback = QgsProcessingFeedback()

    def clip_and_mosaic_rasters(self):
        vector_layer = QgsVectorLayer(self.vector_layer_path, "vector_layer", "ogr")
        if not vector_layer.isValid():
            log("Error loading vector layer.", level=logging.ERROR)
            return

        # Ensure the output directory exists
        os.makedirs(self.clipped_rasters_folder, exist_ok=True)

        clipped_rasters = []

        # Iterate through each raster file in the folder
        for filename in os.listdir(self.raster_folder):
            if filename.endswith(('.tif', '.tiff', '.TIF', '.TIFF')):  # Check for TIFF files, adjust if necessary
                log(f'Clipping: {filename}', level=logging.INFO)
                raster_path = os.path.join(self.raster_folder, filename)
                output_path = os.path.join(self.clipped_rasters_folder, f"clipped_{filename}")
                clipped_rasters.append(output_path)

                # Clip the raster
                self.clip_raster_by_vector(raster_path, vector_layer, output_path)

        # Create a mosaic from the clipped rasters
        params = {
            'INPUT': ';'.join(clipped_rasters),
            'OUTPUT': self.mosaic_output_path
        }

        processing.run("gdal:merge", params, feedback=self.feedback)
        log(f"Mosaic created successfully. Output saved to: {self.mosaic_output_path}", level=logging.INFO)

    def clip_raster_by_vector(self, raster_path, vector_layer, output_path):
        try:
            params = {
                'INPUT': raster_path,
                'MASK': vector_layer,
                'NODATA': None,
                'CROP_TO_CUTLINE': True,
                'KEEP_RESOLUTION': True,
                'OPTIONS': 'COMPRESS=LZW',  # Add compression option here
                'OUTPUT': output_path
            }

            processing.run("gdal:cliprasterbymasklayer", params, feedback=self.feedback)
            if os.path.exists(output_path):
                log("Raster clipped successfully. Output saved to: " + output_path, level=logging.INFO)
            else:
                log("Error during raster clipping operation. Output not found.", level=logging.ERROR)
        except Exception as e:
            log(f"Error during raster clipping operation: {e}", level=logging.ERROR)
