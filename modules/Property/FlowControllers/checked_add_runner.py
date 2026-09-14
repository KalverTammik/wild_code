"""Apply reviewed additions without per-property dialogs; keep network IO off Qt's GUI thread."""
from PyQt5 import sip
from PyQt5.QtCore import pyqtSlot
from qgis.core import QgsFeatureRequest

from .AddBatchRunner import AddBatchRunner
from .MainAddProperties import MainAddPropertiesFlow, BackendPropertyVerifier
from .UpdatePropertyData import UpdatePropertyData
from ....constants.cadastral_fields import Katastriyksus as F
from ....constants.layer_constants import IMPORT_PROPERTY_TAG
from ....languages.language_manager import LanguageManager
from ....languages.translation_keys import TranslationKeys as K
from ....python.workers import FunctionWorker, start_worker
from ....utils.MapTools.MapHelpers import MapHelpers, FeatureActions, ActiveLayersHelper
from ....utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from ....Logs.python_fail_logger import PythonFailLogger


def apply_reviewed_backend(data, uses, import_date, main_date):
    """Recheck existence to avoid duplicates, then apply the reviewed ordinary action."""
    lang = LanguageManager()
    tunnus = data['cadastralUnit']['number']
    info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
    if info.get('exists') is None:
        raise RuntimeError(lang.translate(K.PROPERTY_ADD_LOOKUP_FAILED))
    if info.get('archived_only') or int(info.get('active_count') or 0) > 1:
        raise RuntimeError(lang.translate(K.PROPERTY_ADD_AMBIGUOUS))
    if info['exists'] is False:
        if not MainAddPropertiesFlow.add_single_property_item(data, uses):
            raise RuntimeError(lang.translate(K.PROPERTY_ADD_WRITE_FAILED))
        return
    item = info.get('property') or {}
    if not item.get('id'):
        raise RuntimeError(lang.translate(K.PROPERTY_ADD_LOOKUP_FAILED))
    same = (str(item.get('cadastralUnitNumber')) == str(tunnus)
            and str(item.get('displayAddress') or '').strip() == str(data['address'].get('street') or '').strip())
    if same or MainAddPropertiesFlow._is_import_newer(import_date, info.get('LastUpdated'), main_date):
        if not UpdatePropertyData.update_single_property_item(item['id'], data, uses):
            raise RuntimeError(lang.translate(K.PROPERTY_ADD_WRITE_FAILED))


class CheckedAddBatchRunner(AddBatchRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._in_flight = False
        self._finished = False
        self._succeeded = 0
        self._errors = []
        self._current = None
        self._worker = None

    def cancel(self):
        if self._finished:
            return
        self._stop_requested = True
        self._queue.clear()
        self._timer.stop()
        # An in-flight mutation cannot be undone. Account for it before finishing.
        if not self._in_flight:
            self._finish()

    def _finish(self):
        if self._finished:
            return
        self._finished = True
        self._dispose_timer()
        self.finished.emit({'canceled': self._stop_requested, 'done': self._done, 'total': self._total,
                            'succeeded': self._succeeded, 'failed': len(self._errors), 'errors': self._errors})

    def _tick(self):
        if self._finished or self._in_flight or self._paused:
            return
        if self._stop_requested or not self._queue:
            self._finish()
            return
        selected = self._queue.pop(0)
        self._current = {'tunnus': ''}
        try:
            tunnus = str(selected.attribute(F.tunnus) or '')
            self._current['tunnus'] = tunnus
            self.progress.emit(self._done, self._total, 'processing', tunnus)
            source = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)
            target = ActiveLayersHelper.resolve_main_property_layer(silent=True)
            if (source is None or target is None or not source.isValid() or not target.isValid()
                    or source is target or source.fields().lookupField(F.tunnus) < 0
                    or target.fields().lookupField(F.tunnus) < 0):
                raise RuntimeError(LanguageManager().translate(K.PROPERTY_ADD_LAYER_CHANGED))
            feature = source.getFeature(selected.id())
            if not feature.isValid() or str(feature.attribute(F.tunnus)) != tunnus:
                raise RuntimeError(LanguageManager().translate(K.PROPERTY_ADD_LAYER_CHANGED))
            # Table features deliberately omit dates/uses/geometry: read the complete source feature.
            data, tunnus, uses, updated = PropertyDataLoader().prepare_data_for_import_stage1(feature)
            matches = self._matches(target, tunnus)
            main_date = matches[0].attribute(F.muudet) if matches and target.fields().lookupField(F.muudet) >= 0 else None
            self._current.update(source=source, target=target, feature=feature,
                                 source_uri=source.source(), target_uri=target.source())
            self._in_flight = True
            self._worker = FunctionWorker(apply_reviewed_backend, data, uses, updated, main_date)
            self._worker.finished.connect(self._backend_done)
            self._worker.error.connect(self._backend_failed)
            start_worker(self._worker)
        except Exception as exc:
            self._complete_item(str(exc))

    @staticmethod
    def _matches(layer, tunnus):
        request = QgsFeatureRequest().setFilterExpression(PropertyDataLoader._eq_expr(F.tunnus, tunnus))
        return list(layer.getFeatures(request))

    @pyqtSlot(object)
    def _backend_done(self, _result):
        try:
            current = self._current
            source, target = current['source'], current['target']
            if (sip.isdeleted(source) or sip.isdeleted(target) or not source.isValid() or not target.isValid()
                    or source is not MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)
                    or target is not ActiveLayersHelper.resolve_main_property_layer(silent=True)
                    or source.source() != current['source_uri'] or target.source() != current['target_uri']):
                raise RuntimeError(LanguageManager().translate(K.PROPERTY_ADD_LAYER_CHANGED))
            # Existing map objects remain unchanged when filling a missing backend record.
            if not self._matches(target, current['tunnus']):
                if source.getFeature(current['feature'].id()) != current['feature']:
                    raise RuntimeError(LanguageManager().translate(K.PROPERTY_ADD_LAYER_CHANGED))
                if target.isEditable() or not target.startEditing():
                    raise RuntimeError(LanguageManager().translate(K.PROPERTY_ADD_MAP_FAILED))
                try:
                    ok, _message = FeatureActions.copy_feature_to_layer(current['feature'], target)
                    if not ok or not target.commitChanges():
                        raise RuntimeError(LanguageManager().translate(K.PROPERTY_ADD_MAP_FAILED))
                except Exception:
                    target.rollBack()
                    raise
            self._complete_item()
        except Exception as exc:
            self._complete_item(str(exc))

    @pyqtSlot(str)
    def _backend_failed(self, message):
        self._complete_item(message)

    def _complete_item(self, error=None):
        self._in_flight = False
        tunnus = self._current['tunnus']
        if error:
            self._errors.append({'tunnus': tunnus, 'message': error})
            PythonFailLogger.log_exception(RuntimeError(error), module='property', event='checked_property_add_failed', extra={'tunnus': tunnus})
        else:
            self._succeeded += 1
        self._done += 1
        self.progress.emit(self._done, self._total, 'processing', tunnus)
        if self._stop_requested or not self._queue:
            self._finish()
        elif not self._paused:
            self._timer.start(self._rest_ms if self._done % self._rest_every == 0 else 0)
