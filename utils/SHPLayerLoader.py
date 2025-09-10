#!/usr/bin/env python3
"""
SHPLayerLoader - Clean Shapefile Loading Utility

This utility provides a clean interface for loading Shapefiles as memory layers
in QGIS, following the pattern suggested in the user requirements.

Author: Wild Code Plugin Team
Date: September 5, 2025
"""

import os
from typing import Optional
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from qgis.core import QgsVectorLayer, Qgis
from qgis.PyQt.QtCore import QSettings

try:
    from ..engines.LayerCreationEngine import get_layer_engine, MailablGroupFolders
    from ..languages.language_manager import LanguageManager
    from ..constants import PROPERTY_TAG, PROPERTIES_BACKGROUND_STYLE, MEMORY_LAYER_SUFFIX
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from engines.LayerCreationEngine import get_layer_engine, MailablGroupFolders
    from languages.language_manager import LanguageManager
    from constants import PROPERTY_TAG, PROPERTIES_BACKGROUND_STYLE, MEMORY_LAYER_SUFFIX


class SHPLayerLoader:
    """
    Clean utility for loading Shapefiles as memory layers in QGIS.

    Provides a simple interface for:
    - File selection dialog
    - Shapefile validation
    - Memory layer creation
    - Group organization
    - Settings persistence
    """

    def __init__(self, parent_widget=None, target_group=None):
        """
        Initialize the SHPLayerLoader.

        Args:
            parent_widget: Parent widget for dialogs
            target_group: Target group name (defaults to NEW_PROPERTIES)
        """
        self.parent = parent_widget
        self.target_group = target_group or MailablGroupFolders.NEW_PROPERTIES
        self.lang_manager = LanguageManager()
        self.engine = get_layer_engine()

    def load_shp_layer(self) -> bool:
        """
        Load a Shapefile as a memory layer with data import.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Show file dialog for SHP files
            file_path = self._get_shp_file_path()
            if not file_path:
                return False  # User cancelled

            # Validate and load the Shapefile
            layer_name = self._get_layer_name_from_path(file_path)
            shp_layer = self._load_shp_layer(file_path, layer_name)

            if not shp_layer:
                 return False

            # Create memory layer and import data
            result = self._create_memory_layer(shp_layer, layer_name)

            if result:
                self._save_settings(layer_name, file_path)

                # Get feature count for success message
                memory_layer = None
                for layer in self.engine.project.mapLayers().values():
                    if layer.name() == result:
                        memory_layer = layer
                        break

                if memory_layer:
                    # Set the property tag on the newly created layer
                    memory_layer.setCustomProperty(PROPERTY_TAG, "true")
                    print(f"[SHPLoader] Set property tag on layer: {memory_layer.name()}")
                    
                    # Ensure layer is not in editing mode before applying style
                    if memory_layer.isEditable():
                        memory_layer.commitChanges()
                    
                    print(f"[SHPLoader] Layer is valid: {memory_layer.isValid()}, in project: {memory_layer in self.engine.project.mapLayers().values()}")
                    
                    # Apply QML style using the engine's centralized method
                    print("[SHPLoader] About to apply QML style via LayerCreationEngine...")
                    style_result = self.engine.apply_qml_style(memory_layer, PROPERTIES_BACKGROUND_STYLE)
                    print(f"[SHPLoader] Style application result: {style_result}")

                feature_count = memory_layer.featureCount() if memory_layer else 0
                self._show_success_message(layer_name, feature_count)
                return True
            else:
                self._show_error_message("Shapefile load failed", "Failed to create memory layer or import data")
                return False

        except Exception as e:
            self._show_error_message("Shapefile loading error", f"Error: {str(e)}")
            return False

    def _get_shp_file_path(self) -> Optional[str]:
        """
        Show file dialog and get Shapefile path.

        Returns:
            Optional[str]: Selected file path or None if cancelled
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent,
            self.lang_manager.translate("Select Shapefile") or "Vali Shapefile fail",
            "",
            "SHP files (*.shp);;All files (*.*)"
        )
        return file_path if file_path else None

    def _get_layer_name_from_path(self, file_path: str) -> str:
        """
        Extract layer name from file path.

        Args:
            file_path: Full path to Shapefile

        Returns:
            str: Layer name without extension
        """
        # Use os.path for proper cross-platform path handling
        return os.path.splitext(os.path.basename(file_path))[0]

    def _load_shp_layer(self, file_path: str, layer_name: str) -> Optional[QgsVectorLayer]:
        """
        Load and validate Shapefile.

        Args:
            file_path: Path to Shapefile
            layer_name: Name for the layer

        Returns:
            Optional[QgsVectorLayer]: Loaded layer or None if invalid
        """
        shp_layer = QgsVectorLayer(file_path, layer_name, 'ogr')

        if not shp_layer.isValid():
            self._show_error_message(
                self.lang_manager.translate("Invalid Shapefile") or "Vigane Shapefile",
                self.lang_manager.translate("Invalid Shapefile message") or "Valitud Shapefile fail ei ole kehtiv."
            )
            return None

        return shp_layer

    def _create_memory_layer(self, shp_layer: QgsVectorLayer, layer_name: str) -> Optional[str]:
        """
        Create memory layer from Shapefile and import the data with optimized batch processing.

        Args:
            shp_layer: Source Shapefile layer
            layer_name: Name for the new memory layer

        Returns:
            Optional[str]: Name of created layer or None if failed
        """
        try:
            memory_layer_name = f"{layer_name}{MEMORY_LAYER_SUFFIX}"

            # Create memory layer with correct structure
            result = self.engine.copy_virtual_layer_for_properties(
                memory_layer_name,
                self.target_group,
                shp_layer
            )

            if not result:
                return None

            # Now import the actual data from Shapefile to memory layer
            memory_layer = None
            for layer in self.engine.project.mapLayers().values():
                if layer.name() == memory_layer_name:
                    memory_layer = layer
                    break

            if not memory_layer:
                print(f"[SHPLoader] Could not find created memory layer: {memory_layer_name}")
                return None

            print(f"[SHPLoader] Found memory layer: {memory_layer.name()}, valid: {memory_layer.isValid()}")
            print(f"[SHPLoader] Memory layer feature count before import: {memory_layer.featureCount()}")
            print(f"[SHPLoader] Source layer fields: {[f.name() for f in shp_layer.fields()]}")
            print(f"[SHPLoader] Memory layer fields: {[f.name() for f in memory_layer.fields()]}")

            # --- verify provider is editable memory ---
            prov_type = getattr(memory_layer, "providerType", lambda: "")()
            if prov_type != "memory":
                print(f"[SHPLoader] Expected 'memory' provider, got '{prov_type}'. "
                      f"Layer likely not editable; cannot import attributes.")
                progress.close()
                return None

            if not memory_layer.isEditable():
                memory_layer.startEditing()

            # --- build a robust field index map: dest_idx -> src_idx ---
            dest_fields = memory_layer.fields()
            src_fields = shp_layer.fields()

            # helper to normalize SHP field names: upper, 10-char truncation
            def shp_norm(name: str) -> str:
                return (name or "").upper()[:10]

            # maps of different normalization strategies
            src_by_exact = {f.name(): i for i, f in enumerate(src_fields)}
            src_by_lower = {f.name().lower(): i for i, f in enumerate(src_fields)}
            src_by_shp = {shp_norm(f.name()): i for i, f in enumerate(src_fields)}

            index_map = []
            for d in dest_fields:
                dn = d.name()
                si = -1
                # try exact
                if dn in src_by_exact:
                    si = src_by_exact[dn]
                # try case-insensitive
                elif dn.lower() in src_by_lower:
                    si = src_by_lower[dn.lower()]
                # try SHP-normalized (UPPER/10 chars)
                elif shp_norm(dn) in src_by_shp:
                    si = src_by_shp[shp_norm(dn)]
                index_map.append(si)

            print(f"[SHPLoader] Field mapping (dest->src): {index_map}")

            # Get total feature count for progress
            total_features = shp_layer.featureCount()

            if total_features == 0:
                # No features to import, just return success
                print("[SHPLoader] No features to import")
                return memory_layer_name

            # Create progress dialog
            from ..widgets.ProgressDialogModern import ProgressDialogModern
            progress = ProgressDialogModern(
                title=self.lang_manager.translate("Importing Shapefile") or "Importing Shapefile",
                maximum=total_features,
                parent=self.parent
            )
            progress.show()

            # PERFORMANCE OPTIMIZATIONS:
            # 1. Use data provider directly for faster bulk operations
            # 2. Disable undo stack for bulk operations (significant performance boost)
            # 3. Batch feature insertion instead of individual adds
            # 4. Scale progress update frequency based on dataset size
            # 5. Add performance timing for monitoring

            import time
            start_time = time.time()

            # Check if memory layer is valid and ready
            if not memory_layer or not memory_layer.isValid():
                print(f"[SHPLoader] Memory layer is not valid")
                progress.close()
                return None

            data_provider = memory_layer.dataProvider()
            if not data_provider:
                print(f"[SHPLoader] Could not get data provider from memory layer")
                progress.close()
                return None

            # For memory layers, we need to be careful with undo stack manipulation
            # Let's try a safer approach
            try:
                original_undo_stack = memory_layer.undoStack()
                # Only disable undo stack if it exists
                if original_undo_stack:
                    memory_layer.setUndoStack(None)
                    undo_stack_disabled = True
                else:
                    undo_stack_disabled = False
            except Exception as e:
                print(f"[SHPLoader] Could not manipulate undo stack: {e}")
                undo_stack_disabled = False
                original_undo_stack = None

            # Determine batch size and progress update frequency based on dataset size
            if total_features <= 1000:
                batch_size = 100
                progress_update_freq = 50
            elif total_features <= 10000:
                batch_size = 500
                progress_update_freq = 200
            else:
                batch_size = 1000
                progress_update_freq = 500

            print(f"[SHPLoader] Using batch size: {batch_size}, progress update frequency: {progress_update_freq}")

            # --- feature batching with fresh QgsFeature objects ---
            from qgis.core import QgsFeature

            batch_features = []
            features_copied = 0

            def flush_batch():
                nonlocal batch_features, features_copied
                if not batch_features:
                    return True
                try:
                    add_res = data_provider.addFeatures(batch_features)
                    # normalize return shape across QGIS versions
                    if isinstance(add_res, tuple):
                        ok = bool(add_res[0])
                    else:
                        ok = bool(add_res)
                    if ok:
                        features_copied += len(batch_features)
                        batch_features = []
                        return True
                    else:
                        # fallback to per-feature adds via layer
                        print("[SHPLoader] Provider bulk add failed; falling back to layer.addFeature()")
                        ok_all = True
                        for f in batch_features:
                            if not memory_layer.addFeature(f):
                                ok_all = False
                        if ok_all:
                            features_copied += len(batch_features)
                        batch_features = []
                        return ok_all
                except Exception as e:
                    print(f"[SHPLoader] addFeatures exception: {e}")
                    # last-resort fallback
                    ok_all = True
                    for f in batch_features:
                        try:
                            if memory_layer.addFeature(f):
                                features_copied += 1
                            else:
                                ok_all = False
                        except Exception as fe:
                            print(f"[SHPLoader] addFeature exception: {fe}")
                            ok_all = False
                    batch_features = []
                    return ok_all

            # iterate source features
            for i, src_feat in enumerate(shp_layer.getFeatures()):
                if progress.wasCanceled():
                    memory_layer.rollBack()
                    progress.close()
                    # Restore undo stack
                    if undo_stack_disabled and original_undo_stack:
                        try:
                            memory_layer.setUndoStack(original_undo_stack)
                        except:
                            pass
                    return None

                # fresh feature with destination schema
                dst_feat = QgsFeature(dest_fields)
                dst_feat.setGeometry(src_feat.geometry())

                # build destination attribute list
                attrs = []
                for si, d_field in zip(index_map, dest_fields):
                    if si >= 0:
                        val = src_feat.attribute(si)
                    else:
                        val = None  # missing field -> NULL
                    attrs.append(val)
                dst_feat.setAttributes(attrs)

                batch_features.append(dst_feat)

                if len(batch_features) >= batch_size:
                    if not flush_batch():
                        print("[SHPLoader] Batch flush failed.")
                        memory_layer.rollBack()
                        progress.close()
                        return None

                # Update progress at optimized frequency
                if i % progress_update_freq == 0 or i == total_features - 1:
                    progress_pct = int((i + 1) / total_features * 100)
                    progress.update(
                        value=i + 1,
                        text1=f"{self.lang_manager.translate('Processing features') or 'Processing features'}: {i + 1}/{total_features} ({progress_pct}%)",
                        text2=f"{self.lang_manager.translate('Features copied') or 'Features copied'}: {features_copied}"
                    )

                    # Process UI events to keep interface responsive
                    from PyQt5.QtWidgets import QApplication
                    QApplication.processEvents()

                    # Additional safety check - ensure progress dialog is still responsive
                    if not progress.isVisible():
                        print("[SHPLoader] Progress dialog was closed unexpectedly")
                        memory_layer.rollBack()
                        if undo_stack_disabled and original_undo_stack:
                            try:
                                memory_layer.setUndoStack(original_undo_stack)
                            except:
                                pass
                        return None

            # flush remaining
            if not flush_batch():
                print("[SHPLoader] Final batch flush failed.")
                memory_layer.rollBack()
                progress.close()
                return None

            # ensure extents are correct for an empty edit buffer path
            memory_layer.updateExtents()

            # Commit changes
            if memory_layer.commitChanges():
                end_time = time.time()
                import_time = end_time - start_time
                features_per_second = features_copied / import_time if import_time > 0 else 0

                progress.update(
                    value=total_features,
                    text1=self.lang_manager.translate("Import complete") or "Import complete",
                    text2=f"{features_copied} {self.lang_manager.translate('features imported') if features_copied != 1 else self.lang_manager.translate('feature imported') or 'features imported'}"
                )
                print(f"[SHPLoader] Successfully imported {features_copied} features from Shapefile using optimized batch processing")
                print(f"[SHPLoader] Import time: {import_time:.2f} seconds ({features_per_second:.1f} features/sec)")
                print(f"[SHPLoader] Final memory layer feature count: {memory_layer.featureCount()}")

                # Verify that attributes were copied correctly
                if memory_layer.featureCount() > 0:
                    first_feature = next(memory_layer.getFeatures())
                    sample_attributes = [first_feature.attribute(field.name()) for field in memory_layer.fields()]
                    print(f"[SHPLoader] Sample attributes from first imported feature: {sample_attributes}")

                # Restore undo stack safely
                if undo_stack_disabled and original_undo_stack:
                    try:
                        memory_layer.setUndoStack(original_undo_stack)
                    except Exception as e:
                        print(f"[SHPLoader] Warning: Could not restore undo stack: {e}")

                # Close progress dialog after a short delay
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(1000, progress.close)

                return memory_layer_name
            else:
                print(f"[SHPLoader] Failed to commit changes to memory layer")
                progress.close()
                memory_layer.rollBack()
                # Restore undo stack safely
                if undo_stack_disabled and original_undo_stack:
                    try:
                        memory_layer.setUndoStack(original_undo_stack)
                    except Exception as e:
                        print(f"[SHPLoader] Warning: Could not restore undo stack: {e}")
                return None

        except Exception as e:
            print(f"[SHPLoader] Error importing data: {e}")
            # Restore undo stack safely in case of exception
            try:
                if undo_stack_disabled and original_undo_stack:
                    memory_layer.setUndoStack(original_undo_stack)
            except:
                pass
            return None

    def _show_success_message(self, layer_name: str, feature_count: int = 0):
        """
        Show success message to user.

        Args:
            layer_name: Name of the successfully loaded layer
            feature_count: Number of features imported
        """
        message = (self.lang_manager.translate("Shapefile loaded with data message") or "Shapefile '{name}' on edukalt laaditud grupis 'Uued kinnistud' ({count} objekti imporditud)")
        if feature_count > 0:
            message = message.format(name=layer_name, count=feature_count)
        else:
            message = (self.lang_manager.translate("Shapefile loaded message") or "Shapefile '{name}' on edukalt laaditud grupis 'Uued kinnistud'").format(name=layer_name)

        QMessageBox.information(
            self.parent,
            self.lang_manager.translate("Shapefile loaded successfully") or "Shapefile edukalt laaditud",
            message  # already formatted above
        )

    def _show_error_message(self, title: str, message: str):
        """
        Show error message to user.

        Args:
            title: Error dialog title
            message: Error message
        """
        QMessageBox.warning(self.parent, title, message)

    def _save_settings(self, layer_name: str, file_path: str):
        """
        Save settings related to the loaded layer.

        Args:
            layer_name: Name of the loaded layer
            file_path: Path to the source file
        """
        try:
            # Save the last loaded file path for future reference
            settings_key = f"wild_code/last_shp_file_{self.target_group}"
            QSettings().setValue(settings_key, file_path)
            
            # Save layer name mapping
            layer_key = f"wild_code/layer_name_{layer_name}"
            QSettings().setValue(layer_key, file_path)
            
            print(f"[SHPLoader] Saved settings for layer: {layer_name}")
            
        except Exception as e:
            print(f"[SHPLoader] Error saving settings: {e}")
