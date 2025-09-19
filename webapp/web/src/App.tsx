import React, { useCallback } from 'react';
import { InputForm } from './components/InputForm';
import { ActionTimeline } from './components/ActionTimeline';
import { AnalysisPanel } from './components/AnalysisPanel';
import { useSSEConnection } from './hooks/useSSEConnection';
import { useAnalysisState } from './hooks/useAnalysisState';
import './App.css';

const App: React.FC = () => {
  const { state, actions } = useAnalysisState();
  const { connect, isLoading } = useSSEConnection({
    onAction: actions.addAction,
    onComplete: actions.setResult,
    onError: actions.setError,
  });

  const handleSubmit = useCallback((prompt: string) => {
    actions.setPrompt(prompt);
    actions.startAnalysis();
    connect(prompt);
  }, [actions, connect]);

  const handleReset = useCallback(() => {
    actions.reset();
  }, [actions]);

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-brand">
            <h1 className="header-title">
              <span className="header-icon">🎯</span>
              PR Analysis Agent
            </h1>
            <p className="header-subtitle">
              AI-powered GitHub Pull Request analyzer with real-time agent visualization
            </p>
          </div>
          <div className="header-stats">
            {state.activeAgents.size > 0 && (
              <div className="active-badge">
                <span className="pulse-indicator" />
                {state.activeAgents.size} agent{state.activeAgents.size !== 1 ? 's' : ''} active
              </div>
            )}
            {state.completedSteps > 0 && (
              <div className="progress-badge">
                {state.completedSteps} steps completed
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="app-main">
        <section className="input-section">
          <InputForm
            onSubmit={handleSubmit}
            isLoading={isLoading || state.isLoading}
            initialValue={state.prompt}
          />
        </section>

        {state.error && (
          <div className="error-banner" role="alert">
            <span className="error-icon">⚠️</span>
            <span className="error-message">{state.error}</span>
            <button
              className="error-dismiss"
              onClick={() => actions.setError('')}
              aria-label="Dismiss error"
            >
              ✕
            </button>
          </div>
        )}

        <section className="analysis-section">
          <div className="analysis-grid">
            {(state.actions.length > 0 || state.isLoading) && (
              <div className="timeline-column">
                <ActionTimeline
                  actions={state.actions}
                  autoScroll={true}
                  showSourceBadge={true}
                  maxHeight={600}
                />
              </div>
            )}

            {(state.result || state.isLoading || state.error) && (
              <div className="results-column">
                <AnalysisPanel
                  result={state.result}
                  isLoading={state.isLoading}
                  error={state.error}
                />
              </div>
            )}
          </div>

          {!state.isLoading && !state.result && state.actions.length === 0 && !state.error && (
            <div className="welcome-state">
              <div className="welcome-content">
                <div className="welcome-icon">🚀</div>
                <h2>Ready to Analyze</h2>
                <p>Enter a GitHub Pull Request URL above to get started</p>
                <div className="feature-grid">
                  <div className="feature-card">
                    <span className="feature-icon">📋</span>
                    <h3>Smart Summaries</h3>
                    <p>Get comprehensive PR summaries with key details and discussion points</p>
                  </div>
                  <div className="feature-card">
                    <span className="feature-icon">🛡️</span>
                    <h3>Risk Analysis</h3>
                    <p>Identify potential risks, complexity, and test coverage concerns</p>
                  </div>
                  <div className="feature-card">
                    <span className="feature-icon">🎬</span>
                    <h3>Live Timeline</h3>
                    <p>Watch agents work in real-time with detailed action tracking</p>
                  </div>
                  <div className="feature-card">
                    <span className="feature-icon">🔊</span>
                    <h3>Voice Narration</h3>
                    <p>Optional voice-over generation for accessibility and convenience</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </section>
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <div className="footer-links">
            <a href="https://github.com/your-org/pr-summarizer-agent" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
            <a href="https://docs.camel-ai.org" target="_blank" rel="noopener noreferrer">
              CAMEL Docs
            </a>
            <a href="https://aimlapi.com" target="_blank" rel="noopener noreferrer">
              AIML API
            </a>
          </div>
          <div className="footer-info">
            Powered by CAMEL AI Framework & GPT-5
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;