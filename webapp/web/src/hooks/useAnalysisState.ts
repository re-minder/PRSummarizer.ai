import { useReducer, useCallback } from 'react';
import { Action, AnalysisResult } from './useSSEConnection';

interface AnalysisState {
  prompt: string;
  actions: Action[];
  result: AnalysisResult | null;
  error: string | null;
  isLoading: boolean;
  activeAgents: Set<string>;
  completedSteps: number;
  totalSteps: number;
}

type AnalysisAction =
  | { type: 'SET_PROMPT'; payload: string }
  | { type: 'START_ANALYSIS' }
  | { type: 'ADD_ACTION'; payload: Action }
  | { type: 'SET_RESULT'; payload: AnalysisResult }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'RESET' }
  | { type: 'UPDATE_PROGRESS'; payload: { completed: number; total: number } };

const initialState: AnalysisState = {
  prompt: '',
  actions: [],
  result: null,
  error: null,
  isLoading: false,
  activeAgents: new Set(),
  completedSteps: 0,
  totalSteps: 0,
};

const analysisReducer = (state: AnalysisState, action: AnalysisAction): AnalysisState => {
  switch (action.type) {
    case 'SET_PROMPT':
      return { ...state, prompt: action.payload };

    case 'START_ANALYSIS':
      return {
        ...state,
        isLoading: true,
        error: null,
        actions: [],
        result: null,
        activeAgents: new Set(),
        completedSteps: 0,
      };

    case 'ADD_ACTION': {
      const newAction = action.payload;
      const activeAgents = new Set(state.activeAgents);

      // Only count actual AI agents (sources ending with '-agent')
      if (newAction.source && newAction.source.endsWith('-agent')) {
        if (newAction.status === 'running') {
          activeAgents.add(newAction.source);
        } else if (newAction.status === 'completed') {
          activeAgents.delete(newAction.source);
        }
      }

      const completedSteps = state.actions.filter(a => a.status === 'completed').length +
                            (newAction.status === 'completed' ? 1 : 0);

      return {
        ...state,
        actions: [...state.actions, newAction],
        activeAgents,
        completedSteps,
      };
    }

    case 'SET_RESULT':
      return {
        ...state,
        result: action.payload,
        isLoading: false,
        activeAgents: new Set(),
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
        activeAgents: new Set(),
      };

    case 'UPDATE_PROGRESS':
      return {
        ...state,
        completedSteps: action.payload.completed,
        totalSteps: action.payload.total,
      };

    case 'RESET':
      return initialState;

    default:
      return state;
  }
};

export const useAnalysisState = () => {
  const [state, dispatch] = useReducer(analysisReducer, initialState);

  const setPrompt = useCallback((prompt: string) => {
    dispatch({ type: 'SET_PROMPT', payload: prompt });
  }, []);

  const startAnalysis = useCallback(() => {
    dispatch({ type: 'START_ANALYSIS' });
  }, []);

  const addAction = useCallback((action: Action) => {
    dispatch({ type: 'ADD_ACTION', payload: action });
  }, []);

  const setResult = useCallback((result: AnalysisResult) => {
    dispatch({ type: 'SET_RESULT', payload: result });
  }, []);

  const setError = useCallback((error: string) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);

  const updateProgress = useCallback((completed: number, total: number) => {
    dispatch({ type: 'UPDATE_PROGRESS', payload: { completed, total } });
  }, []);

  return {
    state,
    actions: {
      setPrompt,
      startAnalysis,
      addAction,
      setResult,
      setError,
      reset,
      updateProgress,
    },
  };
};