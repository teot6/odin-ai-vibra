import React, { useEffect, useMemo, useRef, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_VIBRA_API_URL || 'http://127.0.0.1:8000';
const SESSION_STORAGE_KEY = 'vibra_session_id';

class VibraApiError extends Error {
  constructor(message, { code = 'request_failed', status = 0, details = [], isTimeout = false } = {}) {
    super(message);
    this.name = 'VibraApiError';
    this.code = code;
    this.status = status;
    this.details = details;
    this.isTimeout = isTimeout;
  }
}

const apiRequest = async (path, options = {}) => {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 3500);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      signal: controller.signal
    });

    const payload = await response.json().catch(() => null);

    if (!response.ok) {
      const validationMessage = payload?.error?.details?.[0]?.message;
      throw new VibraApiError(
        validationMessage || payload?.error?.message || 'Vibra could not sync this change.',
        {
          code: payload?.error?.code || 'request_failed',
          status: response.status,
          details: payload?.error?.details || []
        }
      );
    }

    return payload?.ok === true && Object.hasOwn(payload, 'data') ? payload.data : payload;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new VibraApiError('The Vibra API took too long to respond.', {
        code: 'timeout',
        isTimeout: true
      });
    }
    if (error instanceof VibraApiError) {
      throw error;
    }
    throw new VibraApiError('The Vibra API is currently unavailable.', {
      code: 'offline'
    });
  } finally {
    window.clearTimeout(timeoutId);
  }
};

const navItems = [
  { id: 'welcome-gate', label: 'Home' },
  { id: 'personality-preview', label: 'Tests' },
  { id: 'match-preview', label: 'Matches' },
  { id: 'ai-chat-preview', label: 'AI Chat' },
  { id: 'vip-preview', label: 'VIP' }
];

const personalityQuestions = [
  {
    dimension: 'Emotional style',
    detail: 'How you process and share feelings',
    question: 'When something matters to you, how do you usually respond?',
    options: ['I talk it through', 'I reflect first', 'It depends on the moment']
  },
  {
    dimension: 'Communication style',
    detail: 'How you listen, speak, and resolve tension',
    question: 'What helps you feel understood in a difficult conversation?',
    options: ['Direct honesty', 'Gentle reassurance', 'Time and clear examples']
  },
  {
    dimension: 'Attachment style',
    detail: 'How you build trust and emotional closeness',
    question: 'What creates a sense of security for you?',
    options: ['Steady contact', 'Quality time', 'Space with consistency']
  },
  {
    dimension: 'Social energy',
    detail: 'How you recharge and connect with others',
    question: 'What sounds like the best weekend rhythm?',
    options: ['A lively plan', 'A quiet reset', 'A mix of both']
  },
  {
    dimension: 'Relationship goals',
    detail: 'What commitment and partnership mean to you',
    question: 'What are you hoping to build right now?',
    options: ['A committed relationship', 'A meaningful connection', 'I am exploring']
  }
];

const answerScores = {
  'I talk it through': { emotional: 'Open processor', openness: 3, expressiveness: 3, adaptability: 1 },
  'I reflect first': { emotional: 'Reflective processor', openness: 2, expressiveness: 1, adaptability: 2 },
  'It depends on the moment': { emotional: 'Adaptive processor', openness: 2, expressiveness: 2, adaptability: 3 },
  'Direct honesty': { communication: 'Clear and direct', expressiveness: 3, adaptability: 1 },
  'Gentle reassurance': { communication: 'Warm and reassuring', expressiveness: 2, adaptability: 2 },
  'Time and clear examples': { communication: 'Thoughtful and precise', expressiveness: 1, adaptability: 3 },
  'Steady contact': { attachment: 'Consistency-led trust', commitment: 3, adaptability: 1 },
  'Quality time': { attachment: 'Presence-led trust', commitment: 2, adaptability: 2 },
  'Space with consistency': { attachment: 'Independent, steady trust', commitment: 2, adaptability: 3 },
  'A lively plan': { social: 'Socially energized', socialEnergy: 3, openness: 2 },
  'A quiet reset': { social: 'Quietly recharging', socialEnergy: 1, openness: 1 },
  'A mix of both': { social: 'Balanced social energy', socialEnergy: 2, openness: 3 },
  'A committed relationship': { goal: 'Committed partnership', commitment: 3 },
  'A meaningful connection': { goal: 'Meaningful connection', commitment: 2 },
  'I am exploring': { goal: 'Open exploration', commitment: 1, adaptability: 3 }
};

const buildPersonalityResult = (answers) => {
  const selectedScores = Object.values(answers).map((answer) => answerScores[answer] || {});
  const total = (key) => selectedScores.reduce((sum, score) => sum + (score[key] || 0), 0);
  const openness = total('openness');
  const expressiveness = total('expressiveness');
  const socialEnergy = total('socialEnergy');
  const commitment = total('commitment');
  const adaptability = total('adaptability');

  let compatibilityProfile = 'Balanced Connector';
  let compatibilityDescription = 'You are likely to connect best with someone who values a mix of closeness, independence, and flexible communication.';

  if (commitment >= 6 && expressiveness >= 5) {
    compatibilityProfile = 'Intentional Communicator';
    compatibilityDescription = 'You are likely to thrive with consistent, emotionally available people who communicate clearly and want to build with purpose.';
  } else if (adaptability >= 7 && openness >= 4) {
    compatibilityProfile = 'Flexible Explorer';
    compatibilityDescription = 'You are likely to connect with curious, self-aware people who respect independence and let a relationship develop naturally.';
  } else if (socialEnergy >= 3 && expressiveness >= 4) {
    compatibilityProfile = 'Expressive Spark';
    compatibilityDescription = 'You are likely to enjoy warm, responsive matches who bring conversational energy and make shared experiences feel easy.';
  } else if (socialEnergy <= 1 && commitment >= 4) {
    compatibilityProfile = 'Quiet Depth Seeker';
    compatibilityDescription = 'You are likely to prefer calm, dependable people who value thoughtful conversation, trust, and meaningful one-to-one time.';
  }

  return {
    communicationStyle: selectedScores.find((score) => score.communication)?.communication || 'Balanced communicator',
    emotionalStyle: selectedScores.find((score) => score.emotional)?.emotional || 'Adaptive processor',
    socialEnergy: selectedScores.find((score) => score.social)?.social || 'Balanced social energy',
    relationshipGoal: selectedScores.find((score) => score.goal)?.goal || 'Meaningful connection',
    attachmentStyle: selectedScores.find((score) => score.attachment)?.attachment || 'Steady trust',
    compatibilityProfile,
    compatibilityDescription,
    scores: { openness, expressiveness, socialEnergy, commitment, adaptability }
  };
};

const matches = [
  {
    name: 'Maya',
    age: 27,
    initials: 'MA',
    score: 94,
    visual: 'match-visual-rose',
    summary: 'Warm, curious, and quietly adventurous.',
    tags: ['Emotionally open', 'Deep communicator', 'Long-term minded'],
    vibe: 'Sunday markets, thoughtful voice notes, live jazz, and conversations that accidentally last until 2 a.m.'
  },
  {
    name: 'Eli',
    age: 31,
    initials: 'EL',
    score: 91,
    visual: 'match-visual-violet',
    summary: 'Grounded, expressive, and socially balanced.',
    tags: ['Secure attachment', 'Playful energy', 'Clear communicator'],
    vibe: 'Cooking for friends, design books, slow travel, and finding the best coffee shop in every neighborhood.'
  },
  {
    name: 'Noa',
    age: 25,
    initials: 'NO',
    score: 88,
    visual: 'match-visual-blue',
    summary: 'Creative, direct, and always learning.',
    tags: ['High empathy', 'Independent spirit', 'Growth focused'],
    vibe: 'Gallery afternoons, spontaneous day trips, clever playlists, and honest conversations with room for laughter.'
  }
];

const initialMessages = [
  {
    author: 'You',
    text: 'I matched with Maya, but I do not want my first message to feel generic.'
  },
  {
    author: 'Vibra AI',
    text: 'Your profiles both value curiosity and thoughtful communication. Try mentioning her love of live jazz and invite an easy, specific answer.'
  },
  {
    author: 'You',
    text: 'Can you give me a respectful example?'
  },
  {
    author: 'Vibra AI',
    text: '"Your jazz-night answer caught my attention. What is one song you would pick to introduce someone to your taste?"'
  }
];

const promptSuggestions = [
  'Help me start a conversation',
  'Explain our compatibility',
  'Suggest a respectful first message'
];

const getMockReply = (message) => {
  const normalized = message.toLowerCase();

  if (normalized.includes('compatibility')) {
    return 'Compatibility is useful context, not certainty. Look at shared values and communication preferences, then stay curious about the real person.';
  }

  if (normalized.includes('first message') || normalized.includes('start')) {
    return 'Try a specific, low-pressure question based on something they shared. Keep it genuine, easy to answer, and respectful of their choice to respond.';
  }

  return 'A good next step is to be clear, kind, and curious. Use this as practice, then let the real conversation develop through mutual interest and consent.';
};

const App = () => {
  const [ageConfirmed, setAgeConfirmed] = useState(false);
  const [activeSection, setActiveSection] = useState('welcome-gate');
  const [testStarted, setTestStarted] = useState(false);
  const [testStep, setTestStep] = useState(0);
  const [personalityAnswers, setPersonalityAnswers] = useState({});
  const [currentMatch, setCurrentMatch] = useState(0);
  const [matchChoices, setMatchChoices] = useState({ liked: [], maybe: [], skipped: [] });
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState(initialMessages);
  const [vipSelection, setVipSelection] = useState('free');
  const [sessionId, setSessionId] = useState('');
  const [syncStatus, setSyncStatus] = useState('saving');
  const [syncMessage, setSyncMessage] = useState('');
  const [sessionReady, setSessionReady] = useState(false);
  const skipRestoredResultSave = useRef(false);
  const saveQueue = useRef(Promise.resolve());
  const recentSaves = useRef(new Map());
  const lastMatchAction = useRef({ key: '', time: 0 });
  const lastChatSubmission = useRef({ key: '', time: 0 });

  const currentQuestion = personalityQuestions[testStep];
  const currentProfile = matches[currentMatch];
  const testComplete = Object.keys(personalityAnswers).length === personalityQuestions.length;
  const personalityResult = useMemo(
    () => (testComplete ? buildPersonalityResult(personalityAnswers) : null),
    [testComplete, personalityAnswers]
  );

  useEffect(() => {
    let cancelled = false;

    const hydrateSession = (session) => {
      setAgeConfirmed(Boolean(session.age_confirmed));
      const restoredAnswers = session.personality_answers || session.personality_result?.answers || {};
      const restoredAnswerCount = Object.keys(restoredAnswers).length;

      if (restoredAnswerCount) {
        setPersonalityAnswers(restoredAnswers);
        setTestStep(Math.min(restoredAnswerCount, personalityQuestions.length - 1));
        setTestStarted(true);
        skipRestoredResultSave.current = restoredAnswerCount === personalityQuestions.length;
      }

      if (Array.isArray(session.match_choices)) {
        const restoredChoices = { liked: [], maybe: [], skipped: [] };
        session.match_choices.forEach((item) => {
          const key = item.choice === 'like' || item.choice === 'yes'
            ? 'liked'
            : item.choice === 'maybe'
              ? 'maybe'
              : 'skipped';
          restoredChoices[key].push(item.match_name);
        });
        setMatchChoices(restoredChoices);
        setCurrentMatch(session.match_choices.length % matches.length);
      }

      if (Array.isArray(session.chat_history) && session.chat_history.length) {
        setChatMessages(session.chat_history.map((item) => ({
          author: item.role === 'user'
            ? 'You'
            : item.role === 'ai'
              ? 'Vibra AI'
              : item.author,
          text: item.message
        })));
      }

      if (session.plan_selection === 'vip' || session.plan_selection === 'free') {
        setVipSelection(session.plan_selection);
      }
    };

    const connectBackend = async () => {
      const legacySessionId = window.localStorage.getItem('vibraSessionId');
      const storedSessionId = window.localStorage.getItem(SESSION_STORAGE_KEY) || legacySessionId;
      const candidateSessionId = storedSessionId || (
        window.crypto?.randomUUID?.().replaceAll('-', '') ||
        `vibra_${Date.now()}_${Math.random().toString(16).slice(2)}`
      );

      window.localStorage.setItem(SESSION_STORAGE_KEY, candidateSessionId);
      window.localStorage.removeItem('vibraSessionId');

      try {
        let session;
        if (storedSessionId) {
          try {
            session = await apiRequest(`/api/vibra/full-state/${storedSessionId}`);
          } catch (error) {
            if (error.status !== 404) {
              throw error;
            }
            session = await apiRequest('/api/vibra/session', {
              method: 'POST',
              body: JSON.stringify({ session_id: storedSessionId })
            });
          }
        } else {
          session = await apiRequest('/api/vibra/session', {
            method: 'POST',
            body: JSON.stringify({ session_id: candidateSessionId })
          });
        }

        if (!cancelled) {
          window.localStorage.setItem(SESSION_STORAGE_KEY, session.session_id);
          setSessionId(session.session_id);
          hydrateSession(session);
          setSessionReady(true);
          setSyncStatus(storedSessionId ? 'restored' : 'synced');
          setSyncMessage(storedSessionId ? 'Your saved demo choices were restored.' : '');
        }
      } catch (error) {
        if (!cancelled) {
          setSessionId(candidateSessionId);
          setSessionReady(true);
          setSyncStatus('offline');
          setSyncMessage(
            error.isTimeout
              ? 'The backend timed out. Your demo still works locally.'
              : 'The backend is unavailable. Your demo still works locally.'
          );
        }
      }
    };

    connectBackend();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!sessionReady || !sessionId || !personalityResult) {
      return;
    }

    if (skipRestoredResultSave.current) {
      skipRestoredResultSave.current = false;
      return;
    }

    setSyncStatus('saving');
    setSyncMessage('');
    apiRequest('/api/vibra/personality-result', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        communication_style: personalityResult.communicationStyle,
        emotional_style: personalityResult.emotionalStyle,
        social_energy: personalityResult.socialEnergy,
        relationship_goal: personalityResult.relationshipGoal,
        compatibility_profile: personalityResult.compatibilityProfile,
        compatibility_description: personalityResult.compatibilityDescription,
        answers: personalityAnswers,
        scores: personalityResult.scores
      })
    }).then(() => {
      setSyncStatus('synced');
      setSyncMessage('');
    }).catch((error) => {
      setSyncStatus('sync-error');
      setSyncMessage(error.message);
    });
  }, [sessionReady, sessionId, personalityResult, personalityAnswers]);

  const persistDemoState = (path, payload, dedupeKey = '') => {
    if (!sessionId) {
      return Promise.resolve();
    }

    const now = Date.now();
    if (dedupeKey && now - (recentSaves.current.get(dedupeKey) || 0) < 700) {
      return Promise.resolve(null);
    }
    if (dedupeKey) {
      recentSaves.current.set(dedupeKey, now);
    }

    setSyncStatus('saving');
    setSyncMessage('');
    const saveRequest = () => apiRequest(path, {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, ...payload })
    });

    const queuedSave = saveQueue.current.then(saveRequest, saveRequest);
    saveQueue.current = queuedSave.catch(() => null);

    return queuedSave.then((result) => {
      setSyncStatus('synced');
      setSyncMessage('');
      return result;
    }).catch((error) => {
      setSyncStatus('sync-error');
      setSyncMessage(
        error.code === 'validation_error'
          ? `Could not sync that change: ${error.message}`
          : error.isTimeout
            ? 'Could not sync before timeout. Your change is kept locally.'
            : 'Could not sync, working locally.'
      );
      return null;
    });
  };

  const navigateTo = (sectionId) => {
    setActiveSection(sectionId);
    window.requestAnimationFrame(() => {
      const target = document.getElementById(sectionId);
      target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      target?.focus({ preventScroll: true });
    });
  };

  const handleNavClick = (event, sectionId) => {
    event.preventDefault();
    navigateTo(sectionId);
  };

  const confirmAge = () => {
    setAgeConfirmed(true);
    persistDemoState('/api/vibra/age-confirmation', { confirmed: true });
    navigateTo('personality-preview');
  };

  const answerQuestion = (answer) => {
    const nextAnswers = {
      ...personalityAnswers,
      [currentQuestion.dimension]: answer
    };
    const nextStep = Math.min(testStep + 1, personalityQuestions.length - 1);
    setPersonalityAnswers(nextAnswers);
    persistDemoState('/api/vibra/personality-progress', {
      answers: nextAnswers,
      step_index: nextStep
    });

    if (testStep < personalityQuestions.length - 1) {
      setTestStep(nextStep);
    }
  };

  const restartTest = () => {
    setPersonalityAnswers({});
    setTestStep(0);
    setTestStarted(true);
    persistDemoState('/api/vibra/personality-progress', { answers: {}, step_index: 0 });
  };

  const resetFrontendState = () => {
    setAgeConfirmed(false);
    setActiveSection('welcome-gate');
    setTestStarted(false);
    setTestStep(0);
    setPersonalityAnswers({});
    setCurrentMatch(0);
    setMatchChoices({ liked: [], maybe: [], skipped: [] });
    setChatInput('');
    setChatMessages(initialMessages);
    setVipSelection('free');
  };

  const resetDemoSession = async () => {
    const previousSessionId = sessionId;
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    window.localStorage.removeItem('vibraSessionId');
    resetFrontendState();
    setSessionReady(false);
    setSyncStatus('saving');
    setSyncMessage('');

    try {
      const session = previousSessionId
        ? await apiRequest(`/api/vibra/reset-session/${previousSessionId}`, { method: 'POST' })
        : await apiRequest('/api/vibra/session', { method: 'POST', body: JSON.stringify({}) });

      window.localStorage.setItem(SESSION_STORAGE_KEY, session.session_id);
      setSessionId(session.session_id);
      setSessionReady(true);
      setSyncStatus('reset');
      setSyncMessage('Reset complete. A fresh demo session is ready.');
    } catch (error) {
      const offlineSessionId = (
        window.crypto?.randomUUID?.().replaceAll('-', '') ||
        `vibra_${Date.now()}_${Math.random().toString(16).slice(2)}`
      );
      window.localStorage.setItem(SESSION_STORAGE_KEY, offlineSessionId);
      setSessionId(offlineSessionId);
      setSessionReady(true);
      setSyncStatus('offline');
      setSyncMessage(
        error.isTimeout
          ? 'Reset locally after the backend timed out.'
          : 'Reset locally. The backend is currently unavailable.'
      );
    }

    navigateTo('welcome-gate');
  };

  const chooseMatch = (choice) => {
    const actionKey = `${currentProfile.name}:${choice}`;
    const now = Date.now();
    if (now - lastMatchAction.current.time < 700) {
      return;
    }
    lastMatchAction.current = { key: actionKey, time: now };

    const choiceKey = choice === 'yes' ? 'liked' : choice === 'maybe' ? 'maybe' : 'skipped';

    setMatchChoices((current) => {
      const cleaned = {
        liked: current.liked.filter((name) => name !== currentProfile.name),
        maybe: current.maybe.filter((name) => name !== currentProfile.name),
        skipped: current.skipped.filter((name) => name !== currentProfile.name)
      };

      return {
        ...cleaned,
        [choiceKey]: [...cleaned[choiceKey], currentProfile.name]
      };
    });

    persistDemoState('/api/vibra/match-choice', {
      match_name: currentProfile.name,
      choice: choice === 'yes' ? 'like' : choice === 'no' ? 'skip' : 'maybe'
    }, `match:${currentProfile.name}:${choice}`);
    setCurrentMatch((index) => (index + 1) % matches.length);
  };

  const submitChatMessage = (event, suggestedMessage) => {
    event?.preventDefault();
    const message = (suggestedMessage ?? chatInput).trim();

    if (!message) {
      return;
    }

    const submissionKey = message.toLowerCase();
    const now = Date.now();
    if (lastChatSubmission.current.key === submissionKey && now - lastChatSubmission.current.time < 900) {
      return;
    }
    lastChatSubmission.current = { key: submissionKey, time: now };

    const reply = getMockReply(message);
    setChatMessages((messages) => [
      ...messages,
      { author: 'You', text: message },
      { author: 'Vibra AI', text: reply }
    ]);
    persistDemoState('/api/vibra/chat-message', { role: 'user', message }, `chat:user:${submissionKey}`)
      .then(() => persistDemoState('/api/vibra/chat-message', { role: 'ai', message: reply }, `chat:ai:${submissionKey}`));
    setChatInput('');
  };

  const selectVip = (selection) => {
    setVipSelection(selection);
    persistDemoState('/api/vibra/plan-selection', { plan: selection });
  };

  return (
    <div className="app-shell">
      <header className="header">
        <nav className="nav" aria-label="Primary navigation">
          <a
            className="nav-brand"
            href="#welcome-gate"
            aria-label="Vibra home"
            onClick={(event) => handleNavClick(event, 'welcome-gate')}
          >
            <span aria-hidden="true">V</span>
            Vibra
          </a>
          <div className="session-controls">
            <span
              className={`backend-status backend-status-${syncStatus}`}
              role="status"
              aria-live="polite"
            >
              <span aria-hidden="true"></span>
              {syncStatus === 'synced'
                ? 'Synced'
                : syncStatus === 'restored'
                  ? 'Restored previous session'
                  : syncStatus === 'saving'
                    ? 'Saving...'
                    : syncStatus === 'sync-error'
                      ? 'Could not sync, working locally'
                      : syncStatus === 'reset'
                        ? 'Reset complete'
                        : 'Offline demo mode'}
            </span>
            <button
              className="reset-session-button"
              type="button"
              aria-label="Reset Vibra demo session"
              onClick={resetDemoSession}
            >
              Reset demo
            </button>
          </div>
          <ul className="nav-list">
            {navItems.map((item) => {
              const isActive = activeSection === item.id;
              return (
                <li key={item.id}>
                  <a
                    href={`#${item.id}`}
                    className={`nav-link${isActive ? ' nav-link-active' : ''}`}
                    aria-current={isActive ? 'page' : undefined}
                    onClick={(event) => handleNavClick(event, item.id)}
                  >
                    {item.label}
                  </a>
                </li>
              );
            })}
          </ul>
        </nav>
      </header>
      {syncMessage && (
        <p className={`sync-notice sync-notice-${syncStatus}`} role="status" aria-live="polite">
          {syncMessage}
        </p>
      )}

      <main className="main">
        <section id="welcome-gate" className="welcome-gate" aria-labelledby="welcome-title" tabIndex="-1">
          <article className="welcome-card">
            <div className="welcome-copy">
              <p className="eyebrow">Welcome to Vibra</p>
              <h1 id="welcome-title">Date deeper. Know yourself better.</h1>
              <p className="welcome-value">
                Discover personality-led matches, practice meaningful conversations with AI,
                and build connections around the values that matter to you.
              </p>
            </div>
            <div className="age-panel" aria-label="Age confirmation">
              <span className="age-badge" aria-hidden="true">18+</span>
              <div>
                <h2>For adults only</h2>
                <p>
                  By entering Vibra, you confirm that you are at least 18 years old
                  and agree to use the community responsibly.
                </p>
              </div>
              <div className="welcome-actions">
                <button
                  className="btn btn-primary"
                  type="button"
                  aria-label="Confirm age and enter Vibra"
                  onClick={confirmAge}
                >
                  {ageConfirmed ? 'Age confirmed' : "I'm 18+ - Enter Vibra"}
                </button>
                <button
                  className="btn btn-secondary"
                  type="button"
                  aria-label="Learn how Vibra supports safety"
                  onClick={() => navigateTo('features-section')}
                >
                  See how it works
                </button>
              </div>
              {ageConfirmed && (
                <p className="confirmed-state" role="status">
                  <span aria-hidden="true">OK</span>
                  Age confirmed for this preview.
                </p>
              )}
              <p className="safety-note">
                <span aria-hidden="true">OK</span>
                Verified profiles, privacy-first matching, and tools that help keep every connection respectful.
              </p>
            </div>
          </article>
        </section>

        <section id="landing-page" className="page-section" aria-labelledby="landing-title" tabIndex="-1">
          <p className="eyebrow">The Vibra experience</p>
          <h2 id="landing-title" className="landing-title">Welcome to Vibra!</h2>
          <p>Find your perfect match based on personality and values.</p>
          <button className="btn" type="button" onClick={() => navigateTo('personality-preview')}>
            Explore Vibra
          </button>
        </section>

        <section id="personality-preview" className="page-section personality-preview" aria-labelledby="personality-title" tabIndex="-1">
          <div className="test-intro">
            <p className="eyebrow">Personality discovery</p>
            <h2 id="personality-title">A clearer picture of how you connect</h2>
            <p>
              Explore the patterns behind your relationships in a guided test designed
              to make compatibility matching more personal and meaningful.
            </p>
            <div className="test-progress">
              <div className="progress-copy">
                <span>{testComplete ? 'Preview complete' : 'Preview progress'}</span>
                <strong>{Math.min(Object.keys(personalityAnswers).length + 1, 5)} of 5</strong>
              </div>
              <div
                className="progress-track"
                role="progressbar"
                aria-label="Personality test preview progress"
                aria-valuemin="0"
                aria-valuemax="5"
                aria-valuenow={Object.keys(personalityAnswers).length}
                aria-valuetext={`${Object.keys(personalityAnswers).length} of 5 questions answered`}
              >
                <span
                  className="progress-fill"
                  style={{ width: `${(Object.keys(personalityAnswers).length / 5) * 100}%` }}
                ></span>
              </div>
            </div>
          </div>

          <article className="dimension-panel" aria-labelledby="dimensions-title">
            <div className="dimension-heading">
              <span className="step-number" aria-hidden="true">
                {String(Math.min(testStep + 1, 5)).padStart(2, '0')}
              </span>
              <div>
                <p className="dimension-kicker">What you will explore</p>
                <h3 id="dimensions-title">Your connection profile</h3>
              </div>
            </div>
            <ul className="dimension-list" aria-label="Personality dimensions included in the test">
              {personalityQuestions.map((item) => (
                <li key={item.dimension} className={personalityAnswers[item.dimension] ? 'dimension-complete' : ''}>
                  <span>{item.dimension}</span>
                  <small>{personalityAnswers[item.dimension] || item.detail}</small>
                </li>
              ))}
            </ul>

            {testStarted && !testComplete && (
              <fieldset className="test-question">
                <legend>{currentQuestion.question}</legend>
                <div className="answer-options">
                  {currentQuestion.options.map((option) => (
                    <button
                      key={option}
                      type="button"
                      aria-label={`Select ${option} for ${currentQuestion.dimension}`}
                      onClick={() => answerQuestion(option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </fieldset>
            )}

            {personalityResult && (
              <div className="personality-result" role="status" aria-labelledby="personality-result-title">
                <div className="result-heading">
                  <div>
                    <p className="dimension-kicker">Your personality result</p>
                    <h3 id="personality-result-title">{personalityResult.compatibilityProfile}</h3>
                  </div>
                  <span aria-hidden="true">5/5</span>
                </div>
                <dl className="result-grid">
                  <div><dt>Communication style</dt><dd>{personalityResult.communicationStyle}</dd></div>
                  <div><dt>Emotional style</dt><dd>{personalityResult.emotionalStyle}</dd></div>
                  <div><dt>Social energy</dt><dd>{personalityResult.socialEnergy}</dd></div>
                  <div><dt>Relationship goal</dt><dd>{personalityResult.relationshipGoal}</dd></div>
                  <div className="result-wide"><dt>Compatibility profile</dt><dd>{personalityResult.compatibilityProfile}</dd></div>
                </dl>
                <p className="result-explanation">{personalityResult.compatibilityDescription}</p>
                <p className="result-match-note">
                  Vibra would use these signals to prioritize matches with complementary
                  communication habits, social rhythm, and relationship intentions.
                </p>
              </div>
            )}

            <div className="match-benefit">
              <span className="benefit-icon" aria-hidden="true">+</span>
              <p>
                Your results refine Vibra&apos;s compatibility insights, helping surface
                verified people whose values, energy, and relationship goals align with yours.
              </p>
            </div>
            <button
              className="btn btn-primary test-cta"
              type="button"
              aria-label={testComplete ? 'Restart the Vibra personality test' : 'Start the Vibra personality test'}
              onClick={testComplete ? restartTest : () => setTestStarted(true)}
              disabled={testStarted && !testComplete}
            >
              {testComplete ? 'Retake personality test' : testStarted ? 'Test in progress' : 'Start personality test'}
            </button>
          </article>
        </section>

        <section id="match-preview" className="page-section match-preview" aria-labelledby="match-preview-title" tabIndex="-1">
          <div className="match-section-heading">
            <div>
              <p className="eyebrow">
                {personalityResult ? `Tuned for ${personalityResult.compatibilityProfile}` : 'Curated for your energy'}
              </p>
              <h2 id="match-preview-title">Meet your strongest matches</h2>
              <p>
                {personalityResult
                  ? `${personalityResult.compatibilityDescription} These sample recommendations now reflect your completed personality result.`
                  : 'Compatibility scores combine personality patterns, communication preferences, and relationship goals to help you start with more meaningful context.'}
              </p>
            </div>
            <span className="verified-note"><span aria-hidden="true">OK</span> Verified adults only</span>
          </div>

          <div className="match-summary" aria-live="polite">
            <span><strong>{matchChoices.liked.length}</strong> liked</span>
            <span><strong>{matchChoices.maybe.length}</strong> maybe</span>
            <span><strong>{matchChoices.skipped.length}</strong> skipped</span>
            <span>Profile {currentMatch + 1} of {matches.length}</span>
          </div>

          <div className="match-card-stage" aria-live="polite">
            <article className="match-card match-card-current">
              <div className={`match-visual ${currentProfile.visual}`} aria-hidden="true">
                <span>{currentProfile.initials}</span>
                <strong>{currentProfile.score}% match</strong>
              </div>
              <div className="match-content">
                <div className="match-identity">
                  <div>
                    <h3>{currentProfile.name}, {currentProfile.age}</h3>
                    <p>{currentProfile.summary}</p>
                  </div>
                  <span className="verified-badge" aria-label="Verified profile">
                    <span aria-hidden="true">OK</span> Verified
                  </span>
                </div>
                <ul className="match-tags" aria-label={`${currentProfile.name}'s personality match traits`}>
                  {currentProfile.tags.map((tag) => <li key={tag}>{tag}</li>)}
                </ul>
                <p className="match-vibe">{currentProfile.vibe}</p>
                <div className="match-actions" aria-label={`Actions for ${currentProfile.name}`}>
                  <button className="match-action match-action-no" type="button" aria-label={`Pass on ${currentProfile.name}`} onClick={() => chooseMatch('no')}>No</button>
                  <button className="match-action match-action-maybe" type="button" aria-label={`Save ${currentProfile.name} for later`} onClick={() => chooseMatch('maybe')}>Maybe</button>
                  <button className="match-action match-action-yes" type="button" aria-label={`Like ${currentProfile.name}`} onClick={() => chooseMatch('yes')}>Yes</button>
                </div>
              </div>
            </article>
          </div>
        </section>

        <section id="ai-chat-preview" className="page-section ai-chat-preview" aria-labelledby="ai-chat-title" tabIndex="-1">
          <div className="ai-chat-intro">
            <p className="eyebrow">Practice without pressure</p>
            <h2 id="ai-chat-title">Find the words before the moment</h2>
            <p>
              Vibra AI helps you practice opening messages, understand what drives a
              compatibility score, and prepare for thoughtful real-world conversations.
            </p>
            <ul className="ai-benefits" aria-label="Ways Vibra AI can help">
              <li>Shape an opener that sounds like you</li>
              <li>Explore shared traits and possible differences</li>
              <li>Practice respectful, confident communication</li>
            </ul>
            <button className="btn btn-primary ai-chat-cta" type="button" aria-label="Focus the Vibra AI chat input" onClick={() => document.getElementById('chat-input')?.focus()}>
              Try AI practice chat
            </button>
          </div>

          <article className="chat-window" aria-labelledby="chat-window-title">
            <header className="chat-header">
              <span className="ai-avatar" aria-hidden="true">V</span>
              <div><h3 id="chat-window-title">Vibra AI</h3><p>Conversation coach</p></div>
              <span className="ai-status"><span aria-hidden="true"></span> Ready</span>
            </header>

            <div className="chat-messages" aria-label="Conversation with Vibra AI" aria-live="polite">
              {chatMessages.map((message, index) => (
                <div key={`${message.author}-${index}`} className={`chat-message ${message.author === 'You' ? 'chat-message-user' : 'chat-message-ai'}`}>
                  <span className="message-author">{message.author}</span>
                  <p>{message.text}</p>
                </div>
              ))}
            </div>

            <div className="prompt-area">
              <p id="suggested-prompts-title">Suggested prompts</p>
              <div className="prompt-chips" aria-labelledby="suggested-prompts-title">
                {promptSuggestions.map((prompt) => (
                  <button key={prompt} type="button" aria-label={`Ask Vibra AI: ${prompt}`} onClick={() => submitChatMessage(null, prompt)}>
                    {prompt}
                  </button>
                ))}
              </div>
            </div>

            <form className="chat-composer" onSubmit={submitChatMessage}>
              <label htmlFor="chat-input">Practice a message</label>
              <div>
                <input
                  id="chat-input"
                  type="text"
                  value={chatInput}
                  onChange={(event) => setChatInput(event.target.value)}
                  placeholder="Ask for respectful conversation help"
                  maxLength="240"
                />
                <button type="submit" aria-label="Send message to Vibra AI" disabled={!chatInput.trim()}>Send</button>
              </div>
            </form>

            <p className="ai-safety-note">
              <span aria-hidden="true">i</span>
              AI chat is for practice and reflection. It never replaces honest,
              consent-based communication with a real person. This demo uses local
              storage, so do not enter personal or sensitive information.
            </p>
          </article>
        </section>

        <section id="vip-preview" className="page-section vip-preview" aria-labelledby="vip-title" tabIndex="-1">
          <div className="vip-intro">
            <p className="eyebrow">Vibra VIP</p>
            <h2 id="vip-title">More insight. More visibility. Still your pace.</h2>
            <p>
              Unlock deeper compatibility tools and thoughtful ways to stand out,
              while keeping every match and conversation grounded in mutual choice.
            </p>
            <div className="vip-trust-row" aria-label="VIP subscription highlights">
              <span><span aria-hidden="true">OK</span> Cancel anytime</span>
              <span><span aria-hidden="true">OK</span> Core matching stays free</span>
            </div>
          </div>

          <article className={`vip-plan${vipSelection === 'vip' ? ' vip-plan-selected' : ''}`} aria-labelledby="vip-plan-title">
            <div className="vip-plan-top">
              <div>
                <span className="vip-plan-label">Most complete experience</span>
                <h3 id="vip-plan-title">VIP Membership</h3>
              </div>
              <span className="vip-mark" aria-hidden="true">V</span>
            </div>
            <div className="vip-price" aria-label="VIP price preview"><strong>$14</strong><span>.99<br />per month</span></div>
            <ul className="vip-benefits" aria-label="Vibra VIP membership benefits">
              {[
                ['Advanced compatibility insights', 'See deeper trait alignment and communication dynamics.'],
                ['More daily match previews', 'Explore a wider set of personality-led recommendations.'],
                ['AI opening message suggestions', 'Get tailored, respectful conversation starters.'],
                ['Profile boost', 'Increase profile discovery during high-activity periods.'],
                ['Verified priority visibility', 'Help your verified profile appear sooner to compatible people.']
              ].map(([title, detail], index) => (
                <li key={title}>
                  <span className="vip-benefit-icon" aria-hidden="true">{String(index + 1).padStart(2, '0')}</span>
                  <div><strong>{title}</strong><small>{detail}</small></div>
                </li>
              ))}
            </ul>
            <div className="vip-actions">
              <button
                className="btn btn-primary vip-upgrade"
                type="button"
                aria-label="Select Vibra VIP preview"
                aria-pressed={vipSelection === 'vip'}
                onClick={() => selectVip('vip')}
              >
                {vipSelection === 'vip' ? 'VIP selected' : 'Upgrade to VIP'}
              </button>
              <button
                className={`vip-free-action${vipSelection === 'free' ? ' vip-free-selected' : ''}`}
                type="button"
                aria-label="Continue using Vibra without VIP"
                aria-pressed={vipSelection === 'free'}
                onClick={() => selectVip('free')}
              >
                {vipSelection === 'free' ? 'Free plan selected' : 'Continue with free'}
              </button>
            </div>
            <p className="vip-selection-status" role="status">
              {vipSelection === 'vip'
                ? 'VIP preview selected. No payment has been started.'
                : 'Free experience selected. VIP remains optional.'}
            </p>
            <p className="vip-optional-note">
              <span aria-hidden="true">i</span>
              VIP is entirely optional. Free members can still complete personality tests,
              receive matches, and connect with verified users.
            </p>
          </article>
        </section>

        <section id="features-section" className="page-section" aria-labelledby="features-title" tabIndex="-1">
          <div className="supporting-section-heading">
            <p className="eyebrow">Built around better connections</p>
            <h2 id="features-title">A safer, more intentional experience</h2>
            <p>Every part of Vibra is designed to add context, clarity, and confidence to modern dating.</p>
          </div>
          <ul>
            <li><article className="feature-card"><span className="feature-icon" aria-hidden="true">18+</span>18+ age gate with legal responsibility confirmation</article></li>
            <li><article className="feature-card"><span className="feature-icon" aria-hidden="true">ID</span>Mobile-first verified profile card interface</article></li>
            <li><article className="feature-card"><span className="feature-icon" aria-hidden="true">Y/N</span>Clear interested, maybe, and pass decisions</article></li>
            <li><article className="feature-card"><span className="feature-icon" aria-hidden="true">NAV</span>Navigation between Home, Tests, Matches, AI Chat, and VIP</article></li>
          </ul>
        </section>

        <section id="compatibility-tests-section" className="page-section" aria-labelledby="tests-title" tabIndex="-1">
          <div className="supporting-section-heading">
            <p className="eyebrow">Go beyond surface chemistry</p>
            <h2 id="tests-title">Compatibility tests</h2>
            <p>Explore the traits, expectations, and values that shape how a relationship feels day to day.</p>
          </div>
          <ul>
            {['Big Five Personality Traits', 'HEXACO Honesty-Humility Test', 'Attachment Style', 'Relationship Expectations', 'Conflict Style', 'Values', 'Intimacy', 'Commitment', 'Communication', 'Lifestyle and Boundaries'].map((test) => <li key={test}>{test}</li>)}
          </ul>
        </section>

        <section id="compatibility-score-card-section" className="page-section" aria-labelledby="score-title" tabIndex="-1">
          <div className="supporting-section-heading">
            <p className="eyebrow">Insight at a glance</p>
            <h2 id="score-title">Compatibility score card</h2>
            <p>Use clear scores as conversation context, not a substitute for getting to know someone.</p>
          </div>
          <table aria-label="Example compatibility scores">
            <tbody>
              <tr><td><strong>Name 1</strong></td><td><strong>Name 2</strong></td><td><strong>Score (0-10)</strong></td></tr>
              <tr><td>88%</td><td>92%</td><td>8/10</td></tr>
            </tbody>
          </table>
        </section>

        <section id="closing-cta" className="page-section closing-cta" aria-labelledby="closing-title" tabIndex="-1">
          <article className="closing-cta-content">
            <p className="eyebrow">Your next connection starts with you</p>
            <h2 id="closing-title">Ready to meet on more than a first impression?</h2>
            <p>Discover your connection style, explore verified matches, and practice conversations at your own pace.</p>
            <div className="closing-actions">
              <button className="btn btn-primary" type="button" aria-label="Start with the Vibra personality test" onClick={() => navigateTo('personality-preview')}>Start with your personality</button>
              <button className="btn btn-secondary" type="button" aria-label="Browse sample Vibra matches" onClick={() => navigateTo('match-preview')}>Browse matches</button>
            </div>
            <p className="closing-trust"><span aria-hidden="true">18+</span>Adults only. Verified profiles. Respect and consent come first.</p>
          </article>
        </section>
      </main>
    </div>
  );
};

export default App;
