from qgis.core import QgsVectorLayer, QgsFeature, QgsProcessingFeedback
from .base_task import BaseTask
from dual_logger import log
import logging


class CreateLayerFromThresholdTask(BaseTask):
    def __init__(self, description, input_layer, area_threshold):
        super().__init__(description)
        self.input_layer = input_layer
        self.area_threshold = area_threshold
        self.filtered_layer = None

    def task(self):
        try:
            # Create a new memory layer with the same CRS and fields as the input layer
            crs = self.input_layer.crs().toWkt()
            fields = self.input_layer.fields()
            output_layer = QgsVectorLayer(
                f"Polygon?crs={crs}", "FilteredPolygons", "memory")
            output_layer_data_provider = output_layer.dataProvider()
            output_layer_data_provider.addAttributes(fields)
            output_layer.updateFields()

            # Iterate through each feature in the input layer
            for feature in self.input_layer.getFeatures():
                geometry = feature.geometry()
                # Check if the feature's geometry area meets the area threshold
                if geometry and geometry.area() >= self.area_threshold:
                    # If it does, add the feature to the new layer
                    new_feature = QgsFeature(fields)
                    new_feature.setGeometry(geometry)
                    for field in fields:
                        new_feature.setAttribute(field.name(), feature[field.name()])
                    output_layer_data_provider.addFeature(new_feature)

            # Update the layer's extent to the features it contains
            output_layer.updateExtents()
            self.filtered_layer = output_layer

            if self.filtered_layer.featureCount() > 0:
                log(f'Task "{self.description()}" completed with {self.filtered_layer.featureCount()} features', level=logging.INFO)
                return True
            else:
                log(f'Task "{self.description()}" found no features meeting the area threshold', level=logging.WARNING)
                return False
        except Exception as e:
            self.exception = e
            log(f'Task "{self.description()}" failed: {e}', level=logging.ERROR)
            return False
