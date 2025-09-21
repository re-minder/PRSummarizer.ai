import React, { useEffect, useRef, useMemo } from 'react';
import { Action } from '../../hooks/useSSEConnection';
import './ActionTimeline.css';

interface ActionTimelineProps {
  actions: Action[];
  maxHeight?: number;
  autoScroll?: boolean;
  showSourceBadge?: boolean;
}

const ACTION_ICONS: Record<string, string> = {
  // Summarizer actions
  summarizer_initialize: '🚀',
  summarizer_agent_create: '🤖',
  summarizer_prompt: '💬',
  summarizer_agent_thinking: '🤔',
  summarizer_generate: '✍️',
  fetch_pr_info: '📥',

  // Risk actions
  risk_agent_initialize: '🧭',
  risk_agent_start: '🛡️',
  risk_agent_generate: '⚠️',
  risk_agent_error: '❌',

  // Voice actions
  voice_generate: '🔊',
  voice_synthesis: '🎙️',

  // Orchestrator actions
  orchestrator_output: '✅',
  orchestrator_route: '🔄',

  // Default
  default: '⚡',
};

const SOURCE_COLORS: Record<string, string> = {
  'summarizer-agent': '#4F46E5',
  'risk-agent': '#DC2626',
  'voice-agent': '#059669',
  'orchestrator-agent': '#7C3AED',
  summarizer: '#4F46E5',
  risk: '#DC2626',
  voice: '#059669',
  orchestrator: '#7C3AED',
  backend: '#6B7280',
  default: '#6B7280',
};

const formatTimestamp = (timestamp: number): string => {
  const date = new Date(timestamp * 1000);
  const timeString = date.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
  const milliseconds = date.getMilliseconds().toString().padStart(3, '0');
  return `${timeString}.${milliseconds}`;
};

const getActionIcon = (action: string): string => {
  return ACTION_ICONS[action] || ACTION_ICONS.default;
};

const getSourceColor = (source?: string): string => {
  if (!source) return SOURCE_COLORS.default;
  return SOURCE_COLORS[source] || SOURCE_COLORS.default;
};

interface ActionItemProps {
  action: Action;
  index: number;
  showSourceBadge?: boolean;
}

const ActionItem: React.FC<ActionItemProps> = React.memo(({ action, index, showSourceBadge }) => {
  const itemRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Animate on mount
    const timer = setTimeout(() => {
      if (itemRef.current) {
        itemRef.current.classList.add('visible');
      }
    }, 50 * Math.min(index, 10));

    return () => clearTimeout(timer);
  }, [index]);

  const statusClass = `status-${action.status}`;
  const isActive = action.status === 'running';

  return (
    <div
      ref={itemRef}
      className={`action-item ${statusClass} ${isActive ? 'active' : ''}`}
      role="listitem"
      aria-label={`${action.action} - ${action.status}`}
    >
      <div className="action-timeline-connector">
        <div className="timeline-line" />
        <div className="timeline-dot">
          <span className="action-icon">{getActionIcon(action.action)}</span>
        </div>
      </div>

      <div className="action-content">
        <div className="action-header">
          <span className="action-timestamp">{formatTimestamp(action.timestamp)}</span>
          {showSourceBadge && action.source && (
            <span
              className="action-source-badge"
              style={{ backgroundColor: getSourceColor(action.source) }}
            >
              {action.source}
            </span>
          )}
          <span className={`action-status-indicator ${statusClass}`}>
            {action.status === 'running' && <span className="pulse-dot" />}
            {action.status}
          </span>
        </div>

        <div className="action-name">{action.action.replace(/_/g, ' ')}</div>

        {action.detail && (
          <div className="action-detail">{action.detail}</div>
        )}

        {isActive && (
          <div className="action-progress-bar">
            <div className="progress-indeterminate" />
          </div>
        )}
      </div>
    </div>
  );
});

ActionItem.displayName = 'ActionItem';

export const ActionTimeline: React.FC<ActionTimelineProps> = ({
  actions,
  maxHeight = 600,
  autoScroll = true,
  showSourceBadge = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const lastActionCountRef = useRef(0);

  // Auto-scroll to bottom when new actions are added
  useEffect(() => {
    if (autoScroll && actions.length > lastActionCountRef.current && containerRef.current) {
      const scrollElement = containerRef.current;
      const isScrolledNearBottom =
        scrollElement.scrollHeight - scrollElement.scrollTop - scrollElement.clientHeight < 100;

      if (isScrolledNearBottom || actions.length === 1) {
        setTimeout(() => {
          scrollElement.scrollTo({
            top: scrollElement.scrollHeight,
            behavior: 'smooth',
          });
        }, 100);
      }
    }
    lastActionCountRef.current = actions.length;
  }, [actions.length, autoScroll]);

  // Group actions by source for visual separation
  const groupedActions = useMemo(() => {
    const groups: { source: string; actions: Action[] }[] = [];
    let currentGroup: { source: string; actions: Action[] } | null = null;

    actions.forEach((action) => {
      const source = action.source || 'default';
      if (!currentGroup || currentGroup.source !== source) {
        currentGroup = { source, actions: [action] };
        groups.push(currentGroup);
      } else {
        currentGroup.actions.push(action);
      }
    });

    return groups;
  }, [actions]);

  const activeAgentsCount = useMemo(() => {
    return new Set(
      actions
        .filter(a => a.status === 'running' && a.source && a.source.endsWith('-agent'))
        .map(a => a.source)
    ).size;
  }, [actions]);

  if (actions.length === 0) {
    return (
      <div className="action-timeline-empty">
        <div className="empty-icon">⏳</div>
        <p>Waiting for analysis to begin...</p>
        <div className="empty-hint">
          Enter a GitHub PR URL above and click "Analyze PR" to start
        </div>
      </div>
    );
  }

  return (
    <div className="action-timeline-container">
      <div className="timeline-header">
        <h3>Agent Activity Timeline</h3>
        {activeAgentsCount > 0 && (
          <div className="active-agents-indicator">
            <span className="pulse-dot" />
            {activeAgentsCount} agent{activeAgentsCount !== 1 ? 's' : ''} active
          </div>
        )}
      </div>

      <div
        ref={containerRef}
        className="action-timeline-scroll"
        style={{ maxHeight: `${maxHeight}px` }}
        role="list"
        aria-label="Agent actions timeline"
      >
        {actions.map((action, index) => (
          <ActionItem
            key={`${action.timestamp}-${index}`}
            action={action}
            index={index}
            showSourceBadge={showSourceBadge}
          />
        ))}
      </div>

      <div className="timeline-footer">
        <span className="action-count">
          {actions.filter(a => a.status === 'completed').length} of {actions.length} completed
        </span>
      </div>
    </div>
  );
};