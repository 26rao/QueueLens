import { useState, useCallback, useEffect } from 'react';
import { api } from '../lib/api';
import { useWebSocket } from './useWebSocket';
import type { DashboardState, DisruptionAction, PreviewResponse } from '../types';

export function useQueueState() {
  const [state, setState] = useState<DashboardState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [disruptionText, setDisruptionText] = useState('');
  const [parsedActions, setParsedActions] = useState<DisruptionAction[] | null>(null);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [applyLoading, setApplyLoading] = useState(false);

  const fetchState = useCallback(async () => {
    try {
      const data = await api.getState();
      setState(data);
      setError(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchState(); }, [fetchState]);

  const handleWsMessage = useCallback((msg: any) => {
    setWsConnected(true);
    if (['queue_updated', 'disruption_applied', 'doctor_status_changed', 'scenario_reset', 'state_updated', 'simulation_tick'].includes(msg.type)) {
      fetchState();
    }
  }, [fetchState]);

  useWebSocket(handleWsMessage);

  const parseDisruption = async () => {
    if (!disruptionText.trim()) return;
    try {
      const res = await api.parseDisruption(disruptionText);
      setParsedActions(res.actions);
      setPreview(null);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const previewDisruption = async () => {
    if (!parsedActions || !state) return;
    setPreviewLoading(true);
    try {
      const res = await api.previewDisruption(parsedActions, state.state_version);
      setPreview(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setPreviewLoading(false);
    }
  };

  const applyDisruption = async () => {
    if (!preview || !state) return;
    setApplyLoading(true);
    try {
      await api.applyDisruption(preview.preview_id, state.state_version);
      setPreview(null);
      setParsedActions(null);
      setDisruptionText('');
      await fetchState();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setApplyLoading(false);
    }
  };

  const reset = async () => {
    try {
      await api.reset();
      setPreview(null);
      setParsedActions(null);
      setDisruptionText('');
      await fetchState();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return {
    state, loading, error, wsConnected,
    disruptionText, setDisruptionText,
    parsedActions, setParsedActions,
    preview, previewLoading, applyLoading,
    parseDisruption, previewDisruption, applyDisruption, reset, fetchState,
  };
}
