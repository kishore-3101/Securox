import { useSyncExternalStore, useEffect } from 'react';
import { eventStore } from '../stores/eventStore';

export function useWebSocket() {
  const state = useSyncExternalStore(
    eventStore.subscribe,
    eventStore.getState,
    eventStore.getState
  );

  useEffect(() => {
    eventStore.init();
  }, []);

  return state;
}
