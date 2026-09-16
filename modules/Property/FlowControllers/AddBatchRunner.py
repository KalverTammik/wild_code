"""Shared property additions: backend IO in workers, map edits on the GUI thread."""
from PyQt5 import sip
from threading import Event
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
from qgis.core import QgsFeatureRequest, QgsVariantUtils

from ....utils.mapandproperties.PropertyTableManager import PropertyTableManager
from .MainAddProperties import MainAddPropertiesFlow, BackendPropertyVerifier
from .UpdatePropertyData import UpdatePropertyData
from .property_import_decisions import ADDRESS_REASONS, classify_property_import
from ....constants.cadastral_fields import Katastriyksus as F
from ....constants.layer_constants import IMPORT_PROPERTY_TAG
from ....languages.language_manager import LanguageManager
from ....languages.translation_keys import TranslationKeys as K
from ....python.workers import FunctionWorker, start_worker
from ....python.api_rate_limit import api_request_context, RequestCancelled
from ....utils.MapTools.MapHelpers import MapHelpers, FeatureActions, ActiveLayersHelper
from ....utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from ....Logs.python_fail_logger import PythonFailLogger


def apply_reviewed_backend(data, uses, import_date, main_date, *, review=None, source_changed=False):
    """Recheck existence to avoid duplicates, then apply the reviewed ordinary action."""
    lang = LanguageManager()
    tunnus = data['cadastralUnit']['number']
    info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
    decision = classify_property_import(data, import_date, main_date, info)
    if decision['action'] == 'error':
        raise RuntimeError(lang.translate(decision['reason']))
    if review is not None:
        if source_changed or info != review['backend_info']:
            decision['changed'] = True
            if decision['action'] != 'needs_decision':
                decision.update(action='needs_decision', reason=K.PROPERTY_IMPORT_CHANGED)
            return decision
        # Explicit approval applies only to this unchanged address conflict.
        if review['reason'] in ADDRESS_REASONS and decision['reason'] == review['reason']:
            decision['action'] = 'update'
    if decision['action'] == 'needs_decision':
        return decision
    if decision['action'] == 'create':
        if not MainAddPropertiesFlow.add_single_property_item(data, uses, raise_on_error=True):
            raise RuntimeError(lang.translate(K.PROPERTY_ADD_WRITE_FAILED))
        return
    if not UpdatePropertyData.update_single_property_item(info['property']['id'], data, uses, raise_on_error=True):
        raise RuntimeError(lang.translate(K.PROPERTY_ADD_WRITE_FAILED))


def _run_reviewed_backend(data, uses, import_date, main_date, cancel_event, on_wait, review, source_changed):
    with api_request_context(cancel_event=cancel_event, on_wait=on_wait):
        try:
            return apply_reviewed_backend(data, uses, import_date, main_date,
                                          review=review, source_changed=source_changed)
        except RequestCancelled as exc:
            # A cancelled wait leaves the current property unfinished, never successful.
            return {'cancelled': True, 'message': str(exc) or LanguageManager().translate(K.PROPERTY_ADD_UNFINISHED)}


class AddBatchRunner(QObject):
    progress = pyqtSignal(int, int, str, str)
    finished = pyqtSignal(dict)
    waiting = pyqtSignal(float, str)

    def __init__(self, table, *, use_filtered_rows=False, review_decisions=None, parent=None):
        super().__init__(parent)
        self._table = table
        self._use_filtered_rows = use_filtered_rows
        self._queue = []
        self._done = self._total = 0
        self._stop_requested = self._paused = False
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._tick)
        self._in_flight = False
        self._finished = False
        self._succeeded = 0
        self._errors = []
        self._current = None
        self._worker = None
        self._cancel_event = Event()
        self._unfinished = None
        self._deferred = []
        self._applied = []
        self._review_decisions = {item['tunnus']: item for item in (review_decisions or [])}

    def _dispose_timer(self):
        self._timer.stop()
        self._timer.timeout.disconnect(self._tick)
        self._timer.deleteLater()

    def start(self) -> None:
        mgr = PropertyTableManager()
        try:
            if self._review_decisions:
                self._queue = [item['feature'] for item in self._review_decisions.values()]
            elif self._use_filtered_rows:
                self._queue = list(mgr.get_all_features(self._table) or [])
            else:
                self._queue = list(mgr.get_selected_features(self._table) or [])
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_batch_get_scope_failed",
            )
            self._queue = []

        self._total = len(self._queue)
        self._done = 0
        self._stop_requested = False
        self._paused = False

        if not self._queue:
            self._finish()
            return

        self.progress.emit(0, self._total, "starting", "")
        self._timer.start(0)

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        if not self._paused:
            return
        self._paused = False
        if not self._timer.isActive():
            self._timer.start(0)

    def cancel(self):
        if self._finished:
            return
        self._stop_requested = True
        self._cancel_event.set()
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
                            'succeeded': self._succeeded, 'failed': len(self._errors), 'errors': self._errors,
                            'pending': self._total - self._done, 'stopped': bool(self._errors),
                            'unfinished': self._unfinished, 'deferred': self._deferred,
                            'applied': self._applied})

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
                                 source_uri=source.source(), target_uri=target.source(),
                                 main_features=matches)
            review = self._review_decisions.get(tunnus)
            source_changed = bool(review and (
                review['source_id'] != source.id() or review['source_uri'] != source.source()
                or review['target_id'] != target.id() or review['target_uri'] != target.source()
                or review['feature'] != feature or review['main_features'] != matches))
            self._in_flight = True
            self._worker = FunctionWorker(_run_reviewed_backend, data, uses, updated, main_date,
                                          self._cancel_event, self.waiting.emit, review, source_changed)
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
        if _result and _result.get('cancelled'):
            self._in_flight = False
            self._unfinished = {'tunnus': self._current['tunnus'], 'message': _result['message']}
            self._finish()
            return
        try:
            current = self._current
            source, target = current['source'], current['target']
            if (sip.isdeleted(source) or sip.isdeleted(target) or not source.isValid() or not target.isValid()
                    or source is not MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)
                    or target is not ActiveLayersHelper.resolve_main_property_layer(silent=True)
                    or source.source() != current['source_uri'] or target.source() != current['target_uri']):
                raise RuntimeError(LanguageManager().translate(K.PROPERTY_ADD_LAYER_CHANGED))
            if _result and _result.get('action') == 'needs_decision':
                matches = current['main_features']
                main = matches[0] if matches else None
                _result.update(feature=current['feature'], main_features=matches,
                               source_id=source.id(), source_uri=current['source_uri'],
                               target_id=target.id(), target_uri=current['target_uri'],
                               main_address=('' if main is None or main.fields().lookupField(F.l_aadress) < 0
                                             or QgsVariantUtils.isNull(main[F.l_aadress])
                                             else str(main[F.l_aadress])))
                self._deferred.append(_result)
                self._complete_item(deferred=True)
                return
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

    def _complete_item(self, error=None, *, deferred=False):
        self._in_flight = False
        tunnus = self._current['tunnus']
        if error:
            self._errors.append({'tunnus': tunnus, 'message': error})
            PythonFailLogger.log_exception(RuntimeError(error), module='property', event='checked_property_add_failed', extra={'tunnus': tunnus})
        elif not deferred:
            self._succeeded += 1
            self._applied.append(tunnus)
        self._done += 1
        self.progress.emit(self._done, self._total, 'processing', tunnus)
        if error or self._stop_requested or not self._queue:
            self._finish()
        elif not self._paused:
            # Physical HTTP requests are paced centrally, not by property-count batches.
            self._timer.start(0)
