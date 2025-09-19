import React, { useState, useCallback, useRef, useEffect } from 'react';
import './InputForm.css';

interface InputFormProps {
  onSubmit: (prompt: string) => void;
  isLoading?: boolean;
  initialValue?: string;
}

const PR_URL_PATTERN = /https?:\/\/github\.com\/[\w-]+\/[\w-]+\/pull\/\d+/;

const EXAMPLE_PROMPTS = [
  'Summarize https://github.com/facebook/react/pull/25741',
  'Analyze risks for https://github.com/vercel/next.js/pull/42069',
  'Give me both summary and risks for https://github.com/microsoft/vscode/pull/165270',
  'Summarize and create voice narration for https://github.com/nodejs/node/pull/45279',
];

const QUICK_ACTIONS = [
  { label: 'Summary Only', icon: '📋', modifier: 'Just summarize' },
  { label: 'Risk Analysis', icon: '🛡️', modifier: 'Focus on risks' },
  { label: 'Full Analysis', icon: '🎯', modifier: 'Provide both summary and risk assessment' },
  { label: 'With Voice', icon: '🔊', modifier: 'and generate voice narration' },
];

export const InputForm: React.FC<InputFormProps> = ({
  onSubmit,
  isLoading = false,
  initialValue = '',
}) => {
  const [prompt, setPrompt] = useState(initialValue);
  const [isValid, setIsValid] = useState(true);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedExample, setSelectedExample] = useState<number>(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateInput = useCallback((value: string) => {
    if (!value.trim()) {
      setIsValid(true); // Empty is valid, just won't submit
      return true;
    }
    const hasUrl = PR_URL_PATTERN.test(value);
    setIsValid(hasUrl);
    return hasUrl;
  }, []);

  const handleSubmit = useCallback((e?: React.FormEvent) => {
    e?.preventDefault();
    if (!prompt.trim() || isLoading) return;

    if (validateInput(prompt)) {
      onSubmit(prompt);
      setShowSuggestions(false);
    }
  }, [prompt, isLoading, validateInput, onSubmit]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setPrompt(value);
    validateInput(value);
    setShowSuggestions(value.length > 0 && !PR_URL_PATTERN.test(value));
  }, [validateInput]);

  const handleQuickAction = useCallback((modifier: string) => {
    if (!prompt.includes('github.com')) {
      inputRef.current?.focus();
      return;
    }

    const baseUrl = prompt.match(PR_URL_PATTERN)?.[0];
    if (baseUrl) {
      const newPrompt = `${modifier} ${baseUrl}`;
      setPrompt(newPrompt);
      setShowSuggestions(false);
    }
  }, [prompt]);

  const handleExampleClick = useCallback((example: string) => {
    setPrompt(example);
    setShowSuggestions(false);
    validateInput(example);
    inputRef.current?.focus();
  }, [validateInput]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (showSuggestions && EXAMPLE_PROMPTS.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedExample(prev =>
          prev < EXAMPLE_PROMPTS.length - 1 ? prev + 1 : prev
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedExample(prev => prev > 0 ? prev - 1 : -1);
      } else if (e.key === 'Enter' && selectedExample >= 0) {
        e.preventDefault();
        handleExampleClick(EXAMPLE_PROMPTS[selectedExample]);
      } else if (e.key === 'Escape') {
        setShowSuggestions(false);
        setSelectedExample(-1);
      }
    }
  }, [showSuggestions, selectedExample, handleExampleClick]);

  useEffect(() => {
    setSelectedExample(-1);
  }, [showSuggestions]);

  const getPlaceholderText = () => {
    const examples = [
      'Summarize https://github.com/org/repo/pull/123',
      'Analyze risks for https://github.com/org/repo/pull/456',
      'Full analysis with voice for https://github.com/org/repo/pull/789',
    ];
    return examples[Math.floor(Math.random() * examples.length)];
  };

  return (
    <div className="input-form-container">
      <form className="input-form" onSubmit={handleSubmit}>
        <div className="input-wrapper">
          <div className={`input-field ${!isValid ? 'invalid' : ''} ${isLoading ? 'loading' : ''}`}>
            <span className="input-icon">🔗</span>
            <input
              ref={inputRef}
              type="text"
              value={prompt}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onFocus={() => setShowSuggestions(prompt.length > 0 && !PR_URL_PATTERN.test(prompt))}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              placeholder={getPlaceholderText()}
              disabled={isLoading}
              aria-label="GitHub PR URL or command"
              aria-invalid={!isValid}
              autoComplete="off"
              spellCheck="false"
            />
            {prompt && !isLoading && (
              <button
                type="button"
                className="clear-button"
                onClick={() => {
                  setPrompt('');
                  setIsValid(true);
                  inputRef.current?.focus();
                }}
                aria-label="Clear input"
              >
                ✕
              </button>
            )}
          </div>

          {!isValid && prompt && (
            <div className="validation-message" role="alert">
              <span className="validation-icon">⚠️</span>
              Please include a valid GitHub PR URL (e.g., https://github.com/org/repo/pull/123)
            </div>
          )}

          {showSuggestions && (
            <div className="suggestions-dropdown">
              <div className="suggestions-header">Try an example:</div>
              {EXAMPLE_PROMPTS.map((example, index) => (
                <button
                  key={index}
                  type="button"
                  className={`suggestion-item ${selectedExample === index ? 'selected' : ''}`}
                  onClick={() => handleExampleClick(example)}
                  onMouseEnter={() => setSelectedExample(index)}
                >
                  <span className="suggestion-icon">💡</span>
                  <span className="suggestion-text">{example}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          type="submit"
          className="submit-button"
          disabled={!prompt.trim() || !isValid || isLoading}
        >
          {isLoading ? (
            <>
              <span className="button-spinner" />
              Processing...
            </>
          ) : (
            <>
              <span className="button-icon">🎯</span>
              Analyze PR
            </>
          )}
        </button>
      </form>

      {prompt && PR_URL_PATTERN.test(prompt) && !isLoading && (
        <div className="quick-actions">
          <span className="quick-actions-label">Quick actions:</span>
          {QUICK_ACTIONS.map((action, index) => (
            <button
              key={index}
              type="button"
              className="quick-action-button"
              onClick={() => handleQuickAction(action.modifier)}
            >
              <span className="quick-action-icon">{action.icon}</span>
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};