from qgis.core import QgsProject, QgsVectorLayer
import processing
from .base_task import BaseTask
from dual_logger import log
import logging

class LoadLayersTask(BaseTask):
    def __init__(self, description, gml_path, layer_names, output_name, attribute_field=None, attribute_value=None):
        super().__init__(description)
        self.gml_path = gml_path
        self.layer_names = layer_names
        self.output_name = output_name
        self.attribute_field = attribute_field
        self.attribute_value = attribute_value
        self.merged_layer = None

    def task(self):
        selected_layers = []

        for name in self.layer_names:
            layer_path = f"{self.gml_path}|layername={name}"
            
            if self.attribute_field and self.attribute_value is not None:
                # Extract features based on the attribute value
                result = processing.run("native:extractbyattribute", {
                    'INPUT': layer_path,
                    'FIELD': self.attribute_field,
                    'OPERATOR': 0,  # 0 corresponds to '=', check the documentation for other operators
                    'VALUE': self.attribute_value,
                    'OUTPUT': 'memory:'
                })
                layer = result['OUTPUT']
            else:
                # Load the entire layer if no attribute filter is provided
                layer = QgsVectorLayer(layer_path, name, 'ogr')

            if not layer.isValid() or layer.featureCount() == 0:
                log(f"Layer {name} is not valid or has no features.", level=logging.ERROR)
                continue

            selected_layers.append(layer)

        if selected_layers:
            # Merge the layers that have passed the filtering
            self.merged_layer = processing.run("native:mergevectorlayers", {
                'LAYERS': selected_layers,
                'CRS': None,
                'OUTPUT': 'memory:'
            })['OUTPUT']

            if not self.merged_layer.isValid():
                log("Failed to merge layers into a valid layer.", level=logging.ERROR)
                return False

            self.merged_layer.setName(self.output_name)
            QgsProject.instance().addMapLayer(self.merged_layer)
            log(f"Successfully merged layers into {self.output_name}", level=logging.INFO)
            return True
        else:
            log("No layers with features to merge after applying attribute filter.", level=logging.WARNING)
            return False
