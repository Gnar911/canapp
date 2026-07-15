from typing import Callable, Optional, Set, Tuple, List
from PySide6.QtCore import QEvent
from ui_sdk.components.pyqt.basic_component.RangeSlider import RangeSliderWithLabels
from can_sdk.canlog_viewmodel import (
	LogContextManager,
	BasicFileLogContext,
	NoFilter,
	MsgFilter,
	SigFilter,
	DirectionFilter,
	ChannelFilter,
)

class FilterTimeScopeSlider(RangeSliderWithLabels):
	def __init__(self, parent=None, ctx_model: LogContextManager | None = None):
		super().__init__(parent)
		self._ctx_model: LogContextManager | None = None
		self._ctx: BasicFileLogContext | None = None
		self._subscribed_ctx_model_ids: Set[int] = set()
		self._subscribed_ctx_ids: Set[int] = set()
		self._suspend_apply = False

		self.slider.installEventFilter(self)
		self.slider.setCursor(self.cursor())

		self.set_viewmodel(ctx_model)

	@staticmethod
	def _normalize_can_ids(can_ids) -> List[int]:
		result: List[int] = []
		seen: Set[int] = set()
		if not can_ids:
			return result
		for raw_can_id in can_ids:
			try:
				can_id = int(raw_can_id)
			except Exception:
				continue
			if can_id in seen:
				continue
			seen.add(can_id)
			result.append(can_id)
		return result

	@staticmethod
	def _normalize_channels(channels) -> List[str]:
		result: List[str] = []
		seen: Set[str] = set()
		if not channels:
			return result
		for channel in channels:
			key = str(channel).strip().lower()
			if not key or key in seen:
				continue
			seen.add(key)
			result.append(key)
		return result

	@staticmethod
	def _extract_sig_filter_signal_ids(signals) -> List[int]:
		signal_ids: List[int] = []
		seen: Set[int] = set()
		if not signals:
			return signal_ids
		for signal_filter in signals:
			signal_id = getattr(signal_filter, "signal_id", None)
			if signal_id is None:
				continue
			try:
				sid = int(signal_id)
			except Exception:
				continue
			if sid in seen:
				continue
			seen.add(sid)
			signal_ids.append(sid)
		return signal_ids

	def _set_full_scope_by_count(self, total_count: int):
		try:
			count = int(total_count)
		except Exception:
			return
		if count <= 1:
			return
		self._suspend_apply = True
		try:
			self.set_index_value(0, count - 1)
		finally:
			self._suspend_apply = False

	@staticmethod
	def _timestamp_bounds_from_loader(loader: Callable[[int, int], list], total_count: int) -> Tuple[Optional[float], Optional[float]]:
		if int(total_count) <= 0:
			return None, None
		first_rows = loader(0, 1)
		if not first_rows:
			return None, None
		last_rows = loader(int(total_count) - 1, 1)
		if not last_rows:
			return None, None
		return float(first_rows[0].timestamp), float(last_rows[0].timestamp)

	@staticmethod
	def _resolve_timestamp_from_loader(loader: Callable[[int, int], list], index: int) -> Optional[float]:
		rows = loader(int(index), 1)
		if not rows:
			return None
		try:
			return float(rows[0].timestamp)
		except Exception:
			return None

	def _bind_sparse(self, first_ts: float, last_ts: float, total_count: int, resolver: Callable[[int], Optional[float]]):
		if total_count <= 0:
			return
		self._suspend_apply = True
		try:
			self.set_sparse_data(float(first_ts), float(last_ts), int(total_count), decimals=6)
			self.set_value_resolver(lambda idx: resolver(int(idx)), debounce_ms=20)
			self._set_full_scope_by_count(total_count)
		finally:
			self._suspend_apply = False

	def _bind_sparse_from_context(self):
		ctx = self._ctx
		if ctx is None:
			return

		d_filelog = getattr(ctx, "d_filelog", None)
		if d_filelog is None:
			return

		fs = getattr(ctx, "filter_state", NoFilter())

		if isinstance(fs, NoFilter):
			first_ts, last_ts = d_filelog.get_first_last_timestamp()
			total_count = int(getattr(d_filelog, "total_lines", 0) or 0)
			if first_ts is None or last_ts is None or total_count <= 0:
				return
			self._bind_sparse(
				first_ts=float(first_ts),
				last_ts=float(last_ts),
				total_count=total_count,
				resolver=lambda idx: d_filelog.get_timestamp_by_row(int(idx)),
			)
			return

		if isinstance(fs, MsgFilter):
			can_ids = self._normalize_can_ids(fs.can_ids)
			if not can_ids:
				return

			is_changed = (fs.mode == MsgFilter.Type.FILTER_MSG_CHANGED)
			if len(can_ids) == 1:
				cid = can_ids[0]
				if is_changed:
					total_count = int(d_filelog.get_changed_count_by_can_id(cid))
					first_ts, last_ts = self._timestamp_bounds_from_loader(
						lambda first, size: d_filelog.get_page_from_can_id_changed_row_indices(cid, first, size),
						total_count,
					)
				else:
					total_count = int(d_filelog.get_total_count_by_can_id(cid))
					first_ts, last_ts = d_filelog.get_first_last_timestamp_by_can_id(cid)
				if first_ts is None or last_ts is None or total_count <= 0:
					return
				self._bind_sparse(
					first_ts=float(first_ts),
					last_ts=float(last_ts),
					total_count=total_count,
					resolver=lambda idx, can_id=cid, changed=is_changed: d_filelog.get_timestamp_by_can_id_row(
						can_id,
						int(idx),
						changed=changed,
					),
				)
				return

			if is_changed:
				total_count = int(d_filelog.get_changed_count_by_can_ids(can_ids))
				first_ts, last_ts = self._timestamp_bounds_from_loader(
					lambda first, size: d_filelog.get_page_from_can_ids_changed_row_indices(can_ids, first, size),
					total_count,
				)
			else:
				total_count = int(d_filelog.get_total_count_by_can_ids(can_ids))
				first_ts, last_ts = d_filelog.get_first_last_timestamp_by_can_ids(can_ids)
			if first_ts is None or last_ts is None or total_count <= 0:
				return
			self._bind_sparse(
				first_ts=float(first_ts),
				last_ts=float(last_ts),
				total_count=total_count,
				resolver=lambda idx, cids=tuple(can_ids), changed=is_changed: d_filelog.get_timestamp_by_can_ids_row(
					list(cids),
					int(idx),
					changed=changed,
				),
			)
			return

		if isinstance(fs, DirectionFilter):
			direction = "Tx" if fs.mode == DirectionFilter.Type.TX_ONLY else "Rx"
			total_count = int(d_filelog.get_total_count_by_direction(direction))
			first_ts, last_ts = self._timestamp_bounds_from_loader(
				lambda first, size: d_filelog.get_page_from_direction_row_indices(direction, first, size),
				total_count,
			)
			if first_ts is None or last_ts is None or total_count <= 0:
				return
			self._bind_sparse(
				first_ts=float(first_ts),
				last_ts=float(last_ts),
				total_count=total_count,
				resolver=lambda idx, d=direction: self._resolve_timestamp_from_loader(
					lambda first, size: d_filelog.get_page_from_direction_row_indices(d, first, size),
					int(idx),
				),
			)
			return

		if isinstance(fs, ChannelFilter):
			channels = self._normalize_channels(fs.channels)
			if not channels:
				return
			if len(channels) == 1:
				channel = channels[0]
				total_count = int(d_filelog.get_total_count_by_channel(channel))
				first_ts, last_ts = self._timestamp_bounds_from_loader(
					lambda first, size: d_filelog.get_page_from_channel_row_indices(channel, first, size),
					total_count,
				)
				if first_ts is None or last_ts is None or total_count <= 0:
					return
				self._bind_sparse(
					first_ts=float(first_ts),
					last_ts=float(last_ts),
					total_count=total_count,
					resolver=lambda idx, ch=channel: d_filelog.get_timestamp_by_channel_row(ch, int(idx)),
				)
				return

			total_count = int(d_filelog.get_total_count_by_channels(channels))
			first_ts, last_ts = self._timestamp_bounds_from_loader(
				lambda first, size: d_filelog.get_page_from_channels_row_indices(channels, first, size),
				total_count,
			)
			if first_ts is None or last_ts is None or total_count <= 0:
				return
			self._bind_sparse(
				first_ts=float(first_ts),
				last_ts=float(last_ts),
				total_count=total_count,
				resolver=lambda idx, chs=tuple(channels): self._resolve_timestamp_from_loader(
					lambda first, size: d_filelog.get_page_from_channels_row_indices(list(chs), first, size),
					int(idx),
				),
			)
			return

		if isinstance(fs, SigFilter):
			dd_filelog = getattr(ctx, "dd_filelog", None)
			if dd_filelog is None:
				return

			signal_ids = self._extract_sig_filter_signal_ids(fs.signals)
			if not signal_ids:
				return

			if fs.mode == SigFilter.Type.FILTER_SIG_CHANGED:
				if len(signal_ids) == 1:
					loader = lambda first, size: dd_filelog.get_page_from_signal_id_changed_row_indices(signal_ids[0], first, size)
				else:
					loader = lambda first, size: dd_filelog.get_page_from_signal_ids_changed_row_indices(signal_ids, first, size)
			else:
				signal_rawvalues = {}
				for signal_filter in fs.signals:
					if signal_filter.signal_id is None or signal_filter.rawvalue is None:
						continue
					sid = int(signal_filter.signal_id)
					signal_rawvalues.setdefault(sid, []).append(int(signal_filter.rawvalue))
				if not signal_rawvalues:
					return
				loader = lambda first, size, m=dict(signal_rawvalues): dd_filelog.get_page_from_signal_ids_row_indices_with_rawvalue_map(
					signal_rawvalues=m,
					first_line=first,
					page_size=size,
					match_mode="or",
				)

			total_count = None
			if hasattr(ctx, "get_total_rows_for_current_filter"):
				try:
					total_count = int(ctx.get_total_rows_for_current_filter())
				except Exception:
					total_count = None
			if total_count is None or total_count <= 0:
				return

			first_ts, last_ts = self._timestamp_bounds_from_loader(loader, total_count)
			if first_ts is None or last_ts is None:
				return

			self._bind_sparse(
				first_ts=float(first_ts),
				last_ts=float(last_ts),
				total_count=int(total_count),
				resolver=lambda idx, fn=loader: self._resolve_timestamp_from_loader(fn, int(idx)),
			)

	def _on_context_filter_state_changed(self, *_):
		self._bind_sparse_from_context()

	def set_context(self, ctx: BasicFileLogContext | None):
		self._ctx = ctx
		if ctx is None:
			return

		ctx_id = id(ctx)
		if ctx_id not in self._subscribed_ctx_ids:
			try:
				ctx.event_on_filter_state_changed.subscribe(self._on_context_filter_state_changed)
				self._subscribed_ctx_ids.add(ctx_id)
			except Exception:
				pass

		self._bind_sparse_from_context()

	def _on_context_changed(self, ctx: BasicFileLogContext | None):
		self.set_context(ctx)

	def set_viewmodel(self, ctx_model: LogContextManager | None):
		self._ctx_model = ctx_model
		if ctx_model is None:
			return

		model_id = id(ctx_model)
		if model_id not in self._subscribed_ctx_model_ids:
			try:
				ctx_model.event_on_context_changed.subscribe(self._on_context_changed)
				self._subscribed_ctx_model_ids.add(model_id)
			except Exception:
				pass

		self.set_context(getattr(ctx_model, "cur_ctx", None))

	def _apply_time_filter_from_slider(self):
		ctx = self._ctx
		if ctx is None:
			return
		if self._suspend_apply:
			return

		lo, hi = self.get_value()
		try:
			ctx.set_time_range_filter(float(lo), float(hi))
		except Exception:
			return

	def eventFilter(self, obj, event):
		if obj is self.slider and event.type() == QEvent.MouseButtonRelease:
			self._apply_time_filter_from_slider()
		return super().eventFilter(obj, event)

