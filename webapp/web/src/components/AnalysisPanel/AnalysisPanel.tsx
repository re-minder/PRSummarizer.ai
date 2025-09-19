import React, { useState, useRef, useCallback } from 'react';
import { AnalysisResult } from '../../hooks/useSSEConnection';
import './AnalysisPanel.css';

interface AnalysisPanelProps {
  result: AnalysisResult | null;
  isLoading?: boolean;
  error?: string | null;
}

interface TabConfig {
  id: keyof AnalysisResult | 'final';
  label: string;
  icon: string;
  field?: keyof AnalysisResult;
}

const TABS: TabConfig[] = [
  { id: 'summary', label: 'Summary', icon: '📋', field: 'summary' },
  { id: 'risk_report', label: 'Risk Analysis', icon: '🛡️', field: 'risk_report' },
  { id: 'final', label: 'Final Output', icon: '🧾', field: 'output' },
];

const formatContent = (content: string): React.ReactNode => {
  // Split content into sections based on headers (lines starting with ##)
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let currentParagraph: string[] = [];

  const flushParagraph = () => {
    if (currentParagraph.length > 0) {
      const text = currentParagraph.join('\n');
      elements.push(
        <p key={elements.length} className="content-paragraph">
          {text}
        </p>
      );
      currentParagraph = [];
    }
  };

  lines.forEach((line) => {
    // Check for headers
    if (line.startsWith('## ')) {
      flushParagraph();
      elements.push(
        <h3 key={elements.length} className="content-header">
          {line.replace('## ', '')}
        </h3>
      );
    } else if (line.startsWith('### ')) {
      flushParagraph();
      elements.push(
        <h4 key={elements.length} className="content-subheader">
          {line.replace('### ', '')}
        </h4>
      );
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      // Handle bullet points
      if (currentParagraph.length > 0 && !currentParagraph[currentParagraph.length - 1].startsWith('- ')) {
        flushParagraph();
      }
      currentParagraph.push(line);
    } else if (line.trim() === '') {
      flushParagraph();
    } else {
      currentParagraph.push(line);
    }
  });

  flushParagraph();
  return elements;
};

export const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
  result,
  isLoading = false,
  error = null,
}) => {
  const [activeTab, setActiveTab] = useState<string>('summary');
  const [copiedSection, setCopiedSection] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const handleCopy = useCallback(async (content: string, section: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedSection(section);
      setTimeout(() => setCopiedSection(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }, []);

  const handlePlayVoice = useCallback(() => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        audioRef.current.play();
        setIsPlaying(true);
      }
    }
  }, [isPlaying]);

  const handleAudioEnded = useCallback(() => {
    setIsPlaying(false);
  }, []);

  if (error) {
    return (
      <div className="analysis-panel error-state">
        <div className="error-icon">⚠️</div>
        <h3>Analysis Error</h3>
        <p>{error}</p>
        <button className="retry-button" onClick={() => window.location.reload()}>
          Try Again
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="analysis-panel">
        <div className="panel-header">
          <h2>Analysis Results</h2>
        </div>
        <div className="loading-skeleton">
          <div className="skeleton-tabs">
            {TABS.map((tab) => (
              <div key={tab.id} className="skeleton-tab" />
            ))}
          </div>
          <div className="skeleton-content">
            <div className="skeleton-line skeleton-header" />
            <div className="skeleton-line" />
            <div className="skeleton-line" />
            <div className="skeleton-line skeleton-short" />
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="analysis-panel empty-state">
        <div className="empty-icon">📝</div>
        <h3>No Analysis Yet</h3>
        <p>Results will appear here once the analysis is complete</p>
      </div>
    );
  }

  const activeContent = activeTab === 'final'
    ? result.output
    : result[activeTab as keyof AnalysisResult] as string;

  return (
    <div className="analysis-panel">
      <div className="panel-header">
        <h2>Analysis Results</h2>
        {result.voice_url && (
          <button
            className={`voice-button ${isPlaying ? 'playing' : ''}`}
            onClick={handlePlayVoice}
            aria-label={isPlaying ? 'Pause voice over' : 'Play voice over'}
          >
            {isPlaying ? '⏸️' : '▶️'} Voice Over
          </button>
        )}
      </div>

      <div className="panel-tabs">
        {TABS.map((tab) => {
          const content = tab.id === 'final'
            ? result.output
            : result[tab.field as keyof AnalysisResult] as string;

          if (!content) return null;

          return (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
              aria-selected={activeTab === tab.id}
              role="tab"
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          );
        })}
      </div>

      <div className="panel-content">
        <div className="content-actions">
          <button
            className="copy-button"
            onClick={() => handleCopy(activeContent, activeTab)}
            aria-label="Copy to clipboard"
          >
            {copiedSection === activeTab ? '✓ Copied!' : '📋 Copy'}
          </button>
        </div>

        <div className="content-display">
          {formatContent(activeContent)}
        </div>
      </div>

      {result.voice_url && (
        <audio
          ref={audioRef}
          src={`${(window as any).REACT_APP_API_URL || 'http://localhost:8000'}${result.voice_url}`}
          onEnded={handleAudioEnded}
          preload="none"
        />
      )}
    </div>
  );
};