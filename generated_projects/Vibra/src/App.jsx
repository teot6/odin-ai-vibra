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
      const localizedMessage = payload?.error?.code === 'validation_error'
        ? 'Изпратените данни не отговарят на демо правилата на Vibra.'
        : 'Vibra не успя да синхронизира промяната.';
      throw new VibraApiError(
        localizedMessage,
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
      throw new VibraApiError('Vibra API не отговори навреме.', {
        code: 'timeout',
        isTimeout: true
      });
    }
    if (error instanceof VibraApiError) {
      throw error;
    }
    throw new VibraApiError('Vibra API в момента не е достъпен.', {
      code: 'offline'
    });
  } finally {
    window.clearTimeout(timeoutId);
  }
};

const navItems = [
  { id: 'welcome-gate', label: 'Начало' },
  { id: 'personality-preview', label: 'Тест' },
  { id: 'match-preview', label: 'Съвпадения' },
  { id: 'ai-chat-preview', label: 'AI чат' },
  { id: 'vip-preview', label: 'VIP' }
];

const personalityQuestions = [
  {
    dimension: 'Emotional style',
    label: 'Емоционално изразяване',
    detail: 'Как преживяваш и споделяш чувствата си',
    question: 'Когато нещо е важно за теб, как реагираш най-често?',
    options: [
      ['I talk it through', 'Говоря открито за него'],
      ['I reflect first', 'Първо го обмислям насаме'],
      ['It depends on the moment', 'Зависи от момента']
    ]
  },
  {
    dimension: 'Communication style',
    label: 'Комуникация',
    detail: 'Как слушаш, говориш и създаваш яснота',
    question: 'Какво ти помага да се почувстваш разбран/а в труден разговор?',
    options: [
      ['Direct honesty', 'Директна честност'],
      ['Gentle reassurance', 'Меко и спокойно уверение'],
      ['Time and clear examples', 'Време и ясни примери']
    ]
  },
  {
    dimension: 'Attachment style',
    label: 'Сигурност и близост',
    detail: 'Как изграждаш доверие и емоционална свързаност',
    question: 'Какво ти носи най-силно усещане за сигурност?',
    options: [
      ['Steady contact', 'Постоянен контакт'],
      ['Quality time', 'Качествено време заедно'],
      ['Space with consistency', 'Лично пространство с постоянство']
    ]
  },
  {
    dimension: 'Social energy',
    label: 'Социална енергия',
    detail: 'Как се зареждаш и свързваш с хората',
    question: 'Кой ритъм за уикенда ти звучи най-добре?',
    options: [
      ['A lively plan', 'Динамична програма'],
      ['A quiet reset', 'Тихо презареждане'],
      ['A mix of both', 'Баланс между двете']
    ]
  },
  {
    dimension: 'Relationship goals',
    label: 'Цели във връзката',
    detail: 'Какво означават партньорството и ангажираността за теб',
    question: 'Какво искаш да изградиш в този етап от живота си?',
    options: [
      ['A committed relationship', 'Сериозна връзка'],
      ['A meaningful connection', 'Смислена близост'],
      ['I am exploring', 'Все още изследвам']
    ]
  },
  {
    dimension: 'Conflict handling',
    label: 'Конфликти',
    detail: 'Как преминаваш през напрежение и различия',
    question: 'Когато възникне конфликт, какъв е естественият ти подход?',
    options: [
      ['Address it early', 'Говоря за него навреме'],
      ['Cool down then talk', 'Успокоявам се и после говорим'],
      ['Seek common ground', 'Търся обща основа']
    ]
  },
  {
    dimension: 'Boundaries',
    label: 'Лични граници',
    detail: 'Как пазиш своето пространство и уважаваш чуждото',
    question: 'Как предпочиташ да се договарят границите във връзката?',
    options: [
      ['State boundaries clearly', 'Назоваваме ги ясно'],
      ['Discuss them gently', 'Обсъждаме ги внимателно'],
      ['Adjust as trust grows', 'Настройваме ги с развитието на доверието']
    ]
  },
  {
    dimension: 'Trust',
    label: 'Доверие',
    detail: 'Какво ти помага да се отпуснеш до друг човек',
    question: 'Кое изгражда доверие най-убедително за теб?',
    options: [
      ['Consistent actions', 'Последователни действия'],
      ['Open conversations', 'Открити разговори'],
      ['Time and reliability', 'Време и надеждност']
    ]
  },
  {
    dimension: 'Humor and playfulness',
    label: 'Хумор и лекота',
    detail: 'Каква роля играят смехът и спонтанността',
    question: 'Как изглежда игривостта в добра връзка за теб?',
    options: [
      ['Playful every day', 'Малки закачки всеки ден'],
      ['Warm shared humor', 'Топъл общ хумор'],
      ['Spontaneous adventures', 'Спонтанни приключения']
    ]
  },
  {
    dimension: 'Lifestyle rhythm',
    label: 'Ритъм на живот',
    detail: 'Как организираш ежедневието и свободното си време',
    question: 'Кой ежедневен ритъм ти пасва най-добре?',
    options: [
      ['Planned and steady', 'Планиран и устойчив'],
      ['Flexible and spontaneous', 'Гъвкав и спонтанен'],
      ['Structured with surprises', 'Подреден, но с място за изненади']
    ]
  },
  {
    dimension: 'Introvert-extrovert balance',
    label: 'Интровертност и екстровертност',
    detail: 'Как балансираш общуването и времето насаме',
    question: 'След натоварена седмица как най-лесно възстановяваш енергия?',
    options: [
      ['People recharge me', 'С хора и нови преживявания'],
      ['Solitude recharges me', 'С тишина и време насаме'],
      ['I need both', 'Имам нужда и от двете']
    ]
  },
  {
    dimension: 'Romantic pace',
    label: 'Темпо на сближаване',
    detail: 'Колко бързо допускаш романтична близост',
    question: 'Как предпочиташ да се развива една нова връзка?',
    options: [
      ['Slow and intentional', 'Бавно и осъзнато'],
      ['Natural and responsive', 'Естествено, според взаимността'],
      ['Fast when it feels right', 'Бързо, когато усещането е правилно']
    ]
  },
  {
    dimension: 'Honesty and directness',
    label: 'Честност и директност',
    detail: 'Как поднасяш истината с грижа',
    question: 'Как искаш партньорът ти да споделя трудна истина?',
    options: [
      ['Tell me directly', 'Директно и ясно'],
      ['Be kind but clear', 'С грижа, но без заобикаляне'],
      ['Choose the right moment', 'В подходящия момент']
    ]
  },
  {
    dimension: 'Support style',
    label: 'Подкрепа',
    detail: 'Как даваш и получаваш грижа',
    question: 'Когато ти е трудно, каква подкрепа оценяваш най-много?',
    options: [
      ['Listen and stay close', 'Да ме изслушат и да останат до мен'],
      ['Help me solve it', 'Да ми помогнат да намеря решение'],
      ['Give me space then check in', 'Да ми дадат пространство и после да ме потърсят']
    ]
  },
  {
    dimension: 'Long-term compatibility',
    label: 'Дългосрочна съвместимост',
    detail: 'Кое прави партньорството устойчиво във времето',
    question: 'Кое е най-важно за трайна съвместимост?',
    options: [
      ['Shared values', 'Споделени ценности'],
      ['Growth as a team', 'Израстване като екип'],
      ['Respect for differences', 'Уважение към различията']
    ]
  }
];

const answerScores = {
  'I talk it through': [3, 3, 2, 2, 2], 'I reflect first': [2, 1, 1, 2, 3], 'It depends on the moment': [2, 2, 2, 2, 3],
  'Direct honesty': [2, 3, 2, 2, 1], 'Gentle reassurance': [2, 2, 2, 2, 2], 'Time and clear examples': [2, 1, 1, 2, 3],
  'Steady contact': [2, 2, 2, 3, 1], 'Quality time': [2, 2, 2, 3, 2], 'Space with consistency': [2, 1, 1, 2, 3],
  'A lively plan': [2, 2, 3, 2, 2], 'A quiet reset': [1, 1, 1, 2, 2], 'A mix of both': [3, 2, 2, 2, 3],
  'A committed relationship': [2, 2, 2, 3, 1], 'A meaningful connection': [3, 2, 2, 2, 2], 'I am exploring': [3, 2, 2, 1, 3],
  'Address it early': [2, 3, 2, 3, 1], 'Cool down then talk': [2, 1, 1, 2, 3], 'Seek common ground': [3, 2, 2, 3, 3],
  'State boundaries clearly': [2, 3, 2, 3, 1], 'Discuss them gently': [2, 2, 2, 3, 2], 'Adjust as trust grows': [3, 2, 2, 2, 3],
  'Consistent actions': [2, 2, 2, 3, 1], 'Open conversations': [3, 3, 2, 3, 2], 'Time and reliability': [2, 1, 1, 3, 2],
  'Playful every day': [3, 3, 3, 2, 2], 'Warm shared humor': [2, 2, 2, 3, 2], 'Spontaneous adventures': [3, 2, 3, 1, 3],
  'Planned and steady': [1, 2, 1, 3, 1], 'Flexible and spontaneous': [3, 2, 3, 1, 3], 'Structured with surprises': [3, 2, 2, 2, 3],
  'People recharge me': [2, 3, 3, 2, 2], 'Solitude recharges me': [2, 1, 1, 2, 2], 'I need both': [3, 2, 2, 2, 3],
  'Slow and intentional': [2, 1, 1, 3, 2], 'Natural and responsive': [3, 2, 2, 2, 3], 'Fast when it feels right': [3, 3, 3, 1, 2],
  'Tell me directly': [2, 3, 2, 3, 1], 'Be kind but clear': [3, 2, 2, 3, 2], 'Choose the right moment': [2, 1, 1, 2, 3],
  'Listen and stay close': [2, 2, 2, 3, 2], 'Help me solve it': [2, 3, 2, 2, 1], 'Give me space then check in': [3, 1, 1, 2, 3],
  'Shared values': [2, 2, 2, 3, 1], 'Growth as a team': [3, 3, 2, 3, 3], 'Respect for differences': [3, 2, 2, 3, 3]
};

const answerLabels = Object.fromEntries(
  personalityQuestions.flatMap((question) => question.options)
);

const buildPersonalityResult = (answers) => {
  const totals = Object.values(answers).reduce(
    (sum, answer) => (answerScores[answer] || []).map((value, index) => value + sum[index]),
    [0, 0, 0, 0, 0]
  );
  const [openness, expressiveness, socialEnergy, commitment, adaptability] = totals;
  const selected = (dimension) => answers[dimension];

  const communicationStyle = expressiveness >= 37 ? 'Ясен и открит комуникатор' : expressiveness <= 25 ? 'Обмислен и внимателен комуникатор' : 'Топъл и балансиран комуникатор';
  const emotionalStyle = selected('Emotional style') === 'I reflect first' ? 'Рефлективна емоционална дълбочина' : selected('Emotional style') === 'I talk it through' ? 'Открито емоционално изразяване' : 'Адаптивно емоционално изразяване';
  const socialLabel = socialEnergy >= 36 ? 'Социално зареден/а' : socialEnergy <= 25 ? 'Спокойна, интровертна енергия' : 'Баланс между хора и лично време';
  const goalLabel = selected('Relationship goals') === 'A committed relationship' ? 'Осъзнато дългосрочно партньорство' : selected('Relationship goals') === 'I am exploring' ? 'Свободно опознаване с ясни граници' : 'Смислена и автентична близост';

  let compatibilityProfile = 'Баланс и истинска близост';
  let compatibilityDescription = 'Отговорите ти показват зрял баланс между близост, лично пространство и гъвкава комуникация. Най-силна връзка би изградил/а с човек, който е последователен, любопитен и уважава различния ритъм.';

  if (commitment >= 38 && expressiveness >= 34) {
    compatibilityProfile = 'Осъзнат партньор';
    compatibilityDescription = 'Търсиш стабилност без емоционална дистанция. Цениш ясните разговори, надеждността и общата посока, затова най-добре ти пасва човек, който превръща намеренията си в последователни действия.';
  } else if (adaptability >= 38 && openness >= 37) {
    compatibilityProfile = 'Гъвкав изследовател';
    compatibilityDescription = 'Подхождаш към близостта с любопитство и пространство за развитие. Съвместимостта ти е най-силна с осъзнат човек, който общува честно, приема различията и не насилва темпото.';
  } else if (socialEnergy >= 37 && expressiveness >= 35) {
    compatibilityProfile = 'Изразителна искра';
    compatibilityDescription = 'Внасяш енергия, хумор и откритост в отношенията. Вероятно ще се чувстваш най-добре с топъл и отзивчив партньор, който харесва общите преживявания и умее да създава сигурност.';
  } else if (socialEnergy <= 25 && commitment >= 34) {
    compatibilityProfile = 'Тиха дълбочина';
    compatibilityDescription = 'Предпочиташ качество пред шум и близост, която расте с доверие. Най-подходящ е спокоен, надежден човек, който уважава личното време и присъства истински в важните моменти.';
  }

  return {
    communicationStyle,
    emotionalStyle,
    socialEnergy: socialLabel,
    relationshipGoal: goalLabel,
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
    summary: 'Топла, любопитна и тихо авантюристична.',
    tags: ['Емоционално открита', 'Дълбока комуникация', 'Дългосрочна нагласа'],
    vibe: 'Неделни пазари, внимателни гласови съобщения, джаз на живо и разговори, които неусетно продължават до 2 през нощта.'
  },
  {
    name: 'Eli',
    age: 31,
    initials: 'EL',
    score: 91,
    visual: 'match-visual-violet',
    summary: 'Земна, изразителна и социално балансирана личност.',
    tags: ['Сигурна привързаност', 'Игрива енергия', 'Ясна комуникация'],
    vibe: 'Готвене за приятели, книги за дизайн, бавни пътувания и търсене на най-доброто кафе във всеки квартал.'
  },
  {
    name: 'Noa',
    age: 25,
    initials: 'NO',
    score: 88,
    visual: 'match-visual-blue',
    summary: 'Творческа, директна и винаги любопитна.',
    tags: ['Висока емпатия', 'Независим дух', 'Фокус върху развитието'],
    vibe: 'Следобеди в галерии, спонтанни разходки, добри плейлисти и честни разговори с място за смях.'
  }
];

const initialMessages = [
  {
    author: 'Ти',
    text: 'Имам съвпадение с Мая, но не искам първото ми съобщение да звучи шаблонно.'
  },
  {
    author: 'Vibra AI',
    text: 'И двамата цените любопитството и смислената комуникация. Спомени любовта й към джаза и задай лек, конкретен въпрос.'
  },
  {
    author: 'Ти',
    text: 'Може ли уважителен пример?'
  },
  {
    author: 'Vibra AI',
    text: '„Отговорът ти за джаз вечерите ми направи впечатление. Коя песен би избрала, за да покажеш на някого музикалния си вкус?“'
  }
];

const promptSuggestions = [
  'Помогни ми да започна разговор',
  'Обясни съвместимостта ни',
  'Предложи уважително първо съобщение'
];

const getMockReply = (message) => {
  const normalized = message.toLowerCase();

  if (normalized.includes('съвместимост')) {
    return 'Съвместимостта е полезен ориентир, а не гаранция. Вижте общите ценности и начина си на общуване, но остани любопитен/на към реалния човек.';
  }

  if (normalized.includes('съобщение') || normalized.includes('започна')) {
    return 'Опитай с конкретен и ненатрапчив въпрос, свързан с нещо от профила. Нека бъде искрен, лесен за отговор и с уважение към избора на другия.';
  }

  return 'Добрата следваща стъпка е да бъдеш ясен/на, внимателен/на и любопитен/на. Използвай това като практика, а истинският разговор нека се развие с взаимен интерес и съгласие.';
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
            ? 'Ти'
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
          setSyncMessage(storedSessionId ? 'Запазените ти демо избори са възстановени.' : '');
        }
      } catch (error) {
        if (!cancelled) {
          setSessionId(candidateSessionId);
          setSessionReady(true);
          setSyncStatus('offline');
          setSyncMessage(
            error.isTimeout
              ? 'Локалният сървър не отговори навреме. Демото продължава да работи офлайн.'
              : 'Локалният сървър не е достъпен. Демото продължава да работи офлайн.'
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
          ? `Промяната не беше синхронизирана: ${error.message}`
          : error.isTimeout
            ? 'Синхронизирането изтече. Промяната остава локално.'
            : 'Няма синхронизация. Работиш в локален режим.'
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
      setSyncMessage('Нулирането е готово. Създадена е нова демо сесия.');
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
          ? 'Демото е нулирано локално след изтичане на връзката.'
          : 'Демото е нулирано локално. Сървърът не е достъпен.'
      );
    }

    navigateTo('welcome-gate');
  };

  const chooseMatch = (choice, profile = currentProfile) => {
    const actionKey = `${profile.name}:${choice}`;
    const now = Date.now();
    if (now - lastMatchAction.current.time < 700) {
      return;
    }
    lastMatchAction.current = { key: actionKey, time: now };

    const choiceKey = choice === 'yes' ? 'liked' : choice === 'maybe' ? 'maybe' : 'skipped';

    setMatchChoices((current) => {
      const cleaned = {
        liked: current.liked.filter((name) => name !== profile.name),
        maybe: current.maybe.filter((name) => name !== profile.name),
        skipped: current.skipped.filter((name) => name !== profile.name)
      };

      return {
        ...cleaned,
        [choiceKey]: [...cleaned[choiceKey], profile.name]
      };
    });

    persistDemoState('/api/vibra/match-choice', {
      match_name: profile.name,
      choice: choice === 'yes' ? 'like' : choice === 'no' ? 'skip' : 'maybe'
    }, `match:${profile.name}:${choice}`);
    setCurrentMatch((matches.findIndex((match) => match.name === profile.name) + 1) % matches.length);
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
      { author: 'Ти', text: message },
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
        <nav className="nav" aria-label="Основна навигация">
          <a
            className="nav-brand"
            href="#welcome-gate"
            aria-label="Начало на Vibra"
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
                ? 'Синхронизирано'
                : syncStatus === 'restored'
                  ? 'Сесията е възстановена'
                  : syncStatus === 'saving'
                    ? 'Запазване...'
                    : syncStatus === 'sync-error'
                      ? 'Локален режим'
                      : syncStatus === 'reset'
                        ? 'Нулирано'
                        : 'Офлайн демо'}
            </span>
            <button
              className="reset-session-button"
              type="button"
              aria-label="Нулирай демо сесията на Vibra"
              onClick={resetDemoSession}
            >
              Нулирай
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
              <p className="eyebrow">Добре дошъл/а във Vibra</p>
              <h1 id="welcome-title">Опознавай по-дълбоко. Разбирай себе си по-добре.</h1>
              <p className="welcome-value">
                Откривай съвпадения според характера си, упражнявай смислени разговори с AI
                и създавай връзки около ценностите, които са важни за теб.
              </p>
            </div>
            <div className="age-panel" aria-label="Потвърждение на възрастта">
              <span className="age-badge" aria-hidden="true">18+</span>
              <div>
                <h2>Само за пълнолетни</h2>
                <p>
                  С влизането във Vibra потвърждаваш, че си навършил/а 18 години
                  и ще използваш общността отговорно.
                </p>
              </div>
              <div className="welcome-actions">
                <button
                  className="btn btn-primary"
                  type="button"
                  aria-label="Потвърди възрастта и влез във Vibra"
                  onClick={confirmAge}
                >
                  {ageConfirmed ? 'Възрастта е потвърдена' : 'Навършил/а съм 18 - Вход'}
                </button>
                <button
                  className="btn btn-secondary"
                  type="button"
                  aria-label="Научи как Vibra подкрепя безопасността"
                  onClick={() => navigateTo('features-section')}
                >
                  Виж как работи
                </button>
              </div>
              {ageConfirmed && (
                <p className="confirmed-state" role="status">
                  <span aria-hidden="true">OK</span>
                  Възрастта е потвърдена за това демо.
                </p>
              )}
              <p className="safety-note">
                <span aria-hidden="true">OK</span>
                Верифицирани профили, поверителност и инструменти за уважително общуване.
              </p>
            </div>
          </article>
        </section>

        <section id="landing-page" className="page-section" aria-labelledby="landing-title" tabIndex="-1">
          <p className="eyebrow">Vibra преживяването</p>
          <h2 id="landing-title" className="landing-title">Добре дошъл/а във Vibra!</h2>
          <p>Открий подходящ човек според характера и ценностите си.</p>
          <button className="btn" type="button" onClick={() => navigateTo('personality-preview')}>
            Разгледай Vibra
          </button>
        </section>

        <section id="personality-preview" className="page-section personality-preview" aria-labelledby="personality-title" tabIndex="-1">
          <div className="test-intro">
            <p className="eyebrow">Опознай характера си</p>
            <h2 id="personality-title">По-ясна картина за начина, по който се свързваш</h2>
            <p>
              Разгледай моделите зад отношенията си с по-задълбочен тест,
              създаден да направи съвместимостта по-лична и смислена.
            </p>
            <div className="test-progress">
              <div className="progress-copy">
                <span>{testComplete ? 'Тестът е завършен' : 'Напредък'}</span>
                <strong>{Math.min(Object.keys(personalityAnswers).length + 1, personalityQuestions.length)} от {personalityQuestions.length}</strong>
              </div>
              <div
                className="progress-track"
                role="progressbar"
                aria-label="Напредък на личностния тест"
                aria-valuemin="0"
                aria-valuemax={personalityQuestions.length}
                aria-valuenow={Object.keys(personalityAnswers).length}
                aria-valuetext={`${Object.keys(personalityAnswers).length} от ${personalityQuestions.length} отговорени въпроса`}
              >
                <span
                  className="progress-fill"
                  style={{ width: `${(Object.keys(personalityAnswers).length / personalityQuestions.length) * 100}%` }}
                ></span>
              </div>
            </div>
          </div>

          <article className="dimension-panel" aria-labelledby="dimensions-title">
            <div className="dimension-heading">
              <span className="step-number" aria-hidden="true">
                {String(Math.min(testStep + 1, personalityQuestions.length)).padStart(2, '0')}
              </span>
              <div>
                <p className="dimension-kicker">Какво ще изследваш</p>
                <h3 id="dimensions-title">Твоят профил на свързване</h3>
              </div>
            </div>
            <ul className="dimension-list" aria-label="Измерения в личностния тест">
              {personalityQuestions.map((item) => (
                <li key={item.dimension} className={personalityAnswers[item.dimension] ? 'dimension-complete' : ''}>
                  <span>{item.label}</span>
                  <small>{answerLabels[personalityAnswers[item.dimension]] || item.detail}</small>
                </li>
              ))}
            </ul>

            {testStarted && !testComplete && (
              <fieldset className="test-question">
                <legend>{currentQuestion.question}</legend>
                <div className="answer-options">
                  {currentQuestion.options.map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      aria-label={`Избери „${label}“ за ${currentQuestion.label}`}
                      onClick={() => answerQuestion(value)}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </fieldset>
            )}

            {personalityResult && (
              <div className="personality-result" role="status" aria-labelledby="personality-result-title">
                <div className="result-heading">
                  <div>
                    <p className="dimension-kicker">Твоят личностен резултат</p>
                    <h3 id="personality-result-title">{personalityResult.compatibilityProfile}</h3>
                  </div>
                  <span aria-hidden="true">15/15</span>
                </div>
                <dl className="result-grid">
                  <div><dt>Комуникационен стил</dt><dd>{personalityResult.communicationStyle}</dd></div>
                  <div><dt>Емоционален стил</dt><dd>{personalityResult.emotionalStyle}</dd></div>
                  <div><dt>Социална енергия</dt><dd>{personalityResult.socialEnergy}</dd></div>
                  <div><dt>Цел във връзката</dt><dd>{personalityResult.relationshipGoal}</dd></div>
                  <div className="result-wide"><dt>Профил на съвместимост</dt><dd>{personalityResult.compatibilityProfile}</dd></div>
                </dl>
                <p className="result-explanation">{personalityResult.compatibilityDescription}</p>
                <p className="result-match-note">
                  Vibra използва тези сигнали, за да подреди примерни профили с допълващи се
                  навици за общуване, социален ритъм и намерения за връзка.
                </p>
              </div>
            )}

            <div className="match-benefit">
              <span className="benefit-icon" aria-hidden="true">+</span>
              <p>
                Резултатите ти задълбочават анализа на Vibra и помагат да се откроят
                верифицирани хора с близки ценности, енергия и цели.
              </p>
            </div>
            <button
              className="btn btn-primary test-cta"
              type="button"
              aria-label={testComplete ? 'Започни личностния тест отначало' : 'Започни личностния тест'}
              onClick={testComplete ? restartTest : () => setTestStarted(true)}
              disabled={testStarted && !testComplete}
            >
              {testComplete ? 'Направи теста отново' : testStarted ? 'Тестът е в ход' : 'Започни личностния тест'}
            </button>
          </article>
        </section>

        <section id="match-preview" className="page-section match-preview" aria-labelledby="match-preview-title" tabIndex="-1">
          <div className="match-section-heading">
            <div>
              <p className="eyebrow">
                {personalityResult ? `Настроено за: ${personalityResult.compatibilityProfile}` : 'Подбрано според твоята енергия'}
              </p>
              <h2 id="match-preview-title">Запознай се с най-силните си съвпадения</h2>
              <p>
                {personalityResult
                  ? `${personalityResult.compatibilityDescription} Примерните препоръки вече отразяват завършения ти тест.`
                  : 'Оценките комбинират личностни модели, предпочитания за общуване и цели във връзката, за да започнеш с повече смислен контекст.'}
              </p>
            </div>
            <span className="verified-note"><span aria-hidden="true">OK</span> Само верифицирани пълнолетни</span>
          </div>

          <div className="match-summary" aria-live="polite">
            <span><strong>{matchChoices.liked.length}</strong> харесани</span>
            <span><strong>{matchChoices.maybe.length}</strong> запазени</span>
            <span><strong>{matchChoices.skipped.length}</strong> пропуснати</span>
            <span>Профил {currentMatch + 1} от {matches.length}</span>
          </div>

          <div className="match-card-stage horizontal-card-row" aria-label="Примерни профили за съвпадение" aria-live="polite">
            {matches.map((profile) => (
              <article className="match-card match-card-current" key={profile.name}>
                <div className={`match-visual ${profile.visual}`} aria-hidden="true">
                  <span>{profile.initials}</span>
                  <strong>{profile.score}% съвпадение</strong>
                </div>
                <div className="match-content">
                  <div className="match-identity">
                    <div>
                      <h3>{profile.name}, {profile.age}</h3>
                      <p>{profile.summary}</p>
                    </div>
                    <span className="verified-badge" aria-label="Верифициран профил">
                      <span aria-hidden="true">OK</span> Верифициран
                    </span>
                  </div>
                  <ul className="match-tags" aria-label={`Черти за съвместимост с ${profile.name}`}>
                    {profile.tags.map((tag) => <li key={tag}>{tag}</li>)}
                  </ul>
                  <p className="match-vibe">{profile.vibe}</p>
                  <div className="match-actions" aria-label={`Действия за ${profile.name}`}>
                    <button className="match-action match-action-no" type="button" aria-label={`Пропусни ${profile.name}`} onClick={() => chooseMatch('no', profile)}>Не</button>
                    <button className="match-action match-action-maybe" type="button" aria-label={`Запази ${profile.name} за по-късно`} onClick={() => chooseMatch('maybe', profile)}>Може би</button>
                    <button className="match-action match-action-yes" type="button" aria-label={`Харесай ${profile.name}`} onClick={() => chooseMatch('yes', profile)}>Да</button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section id="ai-chat-preview" className="page-section ai-chat-preview" aria-labelledby="ai-chat-title" tabIndex="-1">
          <div className="ai-chat-intro">
            <p className="eyebrow">Практика без напрежение</p>
            <h2 id="ai-chat-title">Намери точните думи преди момента</h2>
            <p>
              Vibra AI ти помага да упражниш първи съобщения, да разбереш оценката за
              съвместимост и да се подготвиш за смислени реални разговори.
            </p>
            <ul className="ai-benefits" aria-label="Как Vibra AI може да помогне">
              <li>Създай начало, което звучи естествено за теб</li>
              <li>Разгледай общите черти и възможните различия</li>
              <li>Упражни уважително и уверено общуване</li>
            </ul>
            <button className="btn btn-primary ai-chat-cta" type="button" aria-label="Фокусирай полето за Vibra AI чат" onClick={() => document.getElementById('chat-input')?.focus()}>
              Изпробвай AI чата
            </button>
          </div>

          <article className="chat-window" aria-labelledby="chat-window-title">
            <header className="chat-header">
              <span className="ai-avatar" aria-hidden="true">V</span>
              <div><h3 id="chat-window-title">Vibra AI</h3><p>Треньор за разговори</p></div>
              <span className="ai-status"><span aria-hidden="true"></span> Готов</span>
            </header>

            <div className="chat-messages" aria-label="Разговор с Vibra AI" aria-live="polite">
              {chatMessages.map((message, index) => (
                <div key={`${message.author}-${index}`} className={`chat-message ${message.author === 'Ти' ? 'chat-message-user' : 'chat-message-ai'}`}>
                  <span className="message-author">{message.author}</span>
                  <p>{message.text}</p>
                </div>
              ))}
            </div>

            <div className="prompt-area">
              <p id="suggested-prompts-title">Предложени въпроси</p>
              <div className="prompt-chips" aria-labelledby="suggested-prompts-title">
                {promptSuggestions.map((prompt) => (
                  <button key={prompt} type="button" aria-label={`Попитай Vibra AI: ${prompt}`} onClick={() => submitChatMessage(null, prompt)}>
                    {prompt}
                  </button>
                ))}
              </div>
            </div>

            <form className="chat-composer" onSubmit={submitChatMessage}>
              <label htmlFor="chat-input">Упражни съобщение</label>
              <div>
                <input
                  id="chat-input"
                  type="text"
                  value={chatInput}
                  onChange={(event) => setChatInput(event.target.value)}
                  placeholder="Попитай за помощ с разговор"
                  maxLength="240"
                />
                <button type="submit" aria-label="Изпрати съобщение до Vibra AI" disabled={!chatInput.trim()}>Изпрати</button>
              </div>
            </form>

            <p className="ai-safety-note">
              <span aria-hidden="true">i</span>
              AI чатът е за практика и размисъл. Той не заменя честното общуване
              с реален човек и взаимното съгласие. Не въвеждай лична или чувствителна информация.
            </p>
          </article>
        </section>

        <section id="vip-preview" className="page-section vip-preview" aria-labelledby="vip-title" tabIndex="-1">
          <div className="vip-intro">
            <p className="eyebrow">Vibra VIP</p>
            <h2 id="vip-title">Повече яснота. Повече видимост. В твоето темпо.</h2>
            <p>
              Отключи по-задълбочени инструменти за съвместимост и деликатни начини
              да изпъкнеш, без да губиш взаимния избор във всяко общуване.
            </p>
            <div className="vip-trust-row" aria-label="Основни предимства на VIP">
              <span><span aria-hidden="true">OK</span> Отказ по всяко време</span>
              <span><span aria-hidden="true">OK</span> Основните съвпадения остават безплатни</span>
            </div>
          </div>

          <article className={`vip-plan${vipSelection === 'vip' ? ' vip-plan-selected' : ''}`} aria-labelledby="vip-plan-title">
            <div className="vip-plan-top">
              <div>
                <span className="vip-plan-label">Най-пълното изживяване</span>
                <h3 id="vip-plan-title">VIP членство</h3>
              </div>
              <span className="vip-mark" aria-hidden="true">V</span>
            </div>
            <div className="vip-price" aria-label="Примерна VIP цена"><strong>$14</strong><span>.99<br />на месец</span></div>
            <ul className="vip-benefits horizontal-card-row" aria-label="Предимства на Vibra VIP">
              {[
                ['Задълбочена съвместимост', 'Виж по-фини сходства и динамика в общуването.'],
                ['Повече профили дневно', 'Разгледай по-широк подбор според характера си.'],
                ['AI идеи за начало', 'Получи персонални и уважителни предложения.'],
                ['Подсилване на профила', 'Повиши видимостта си в активните часове.'],
                ['Приоритет за верифицирани', 'Профилът ти се показва по-рано на подходящи хора.']
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
                aria-label="Избери демо версията на Vibra VIP"
                aria-pressed={vipSelection === 'vip'}
                onClick={() => selectVip('vip')}
              >
                {vipSelection === 'vip' ? 'VIP е избран' : 'Премини към VIP'}
              </button>
              <button
                className={`vip-free-action${vipSelection === 'free' ? ' vip-free-selected' : ''}`}
                type="button"
                aria-label="Продължи да използваш Vibra без VIP"
                aria-pressed={vipSelection === 'free'}
                onClick={() => selectVip('free')}
              >
                {vipSelection === 'free' ? 'Избран е безплатният план' : 'Продължи безплатно'}
              </button>
            </div>
            <p className="vip-selection-status" role="status">
              {vipSelection === 'vip'
                ? 'Избрано е VIP демо. Не е стартирано плащане.'
                : 'Избрано е безплатното изживяване. VIP остава по избор.'}
            </p>
            <p className="vip-optional-note">
              <span aria-hidden="true">i</span>
              VIP е напълно по избор. Безплатните потребители могат да завършат теста,
              да получават съвпадения и да разглеждат верифицирани профили.
            </p>
          </article>
        </section>

        <section id="features-section" className="page-section" aria-labelledby="features-title" tabIndex="-1">
          <div className="supporting-section-heading">
            <p className="eyebrow">Създадено за по-добри връзки</p>
            <h2 id="features-title">По-сигурно и осъзнато изживяване</h2>
            <p>Всяка част от Vibra добавя контекст, яснота и увереност към модерните запознанства.</p>
          </div>
          <ul>
            <li><article className="feature-card"><span className="feature-icon" aria-hidden="true">18+</span>Потвърждение за пълнолетие и отговорно използване</article></li>
            <li><article className="feature-card"><span className="feature-icon" aria-hidden="true">ID</span>Мобилен интерфейс с примерни верифицирани профили</article></li>
            <li><article className="feature-card"><span className="feature-icon" aria-hidden="true">Д/Н</span>Ясни избори: интерес, може би или пропускане</article></li>
            <li><article className="feature-card"><span className="feature-icon" aria-hidden="true">NAV</span>Навигация между начало, тест, съвпадения, AI чат и VIP</article></li>
          </ul>
        </section>

        <section id="compatibility-tests-section" className="page-section" aria-labelledby="tests-title" tabIndex="-1">
          <div className="supporting-section-heading">
            <p className="eyebrow">Отвъд първоначалната химия</p>
            <h2 id="tests-title">Тестове за съвместимост</h2>
            <p>Разгледай чертите, очакванията и ценностите, които оформят ежедневието на една връзка.</p>
          </div>
          <ul>
            {['Големите пет личностни черти', 'Честност и скромност HEXACO', 'Стил на привързаност', 'Очаквания за връзката', 'Подход към конфликтите', 'Ценности', 'Интимност', 'Ангажираност', 'Комуникация', 'Начин на живот и граници'].map((test) => <li key={test}>{test}</li>)}
          </ul>
        </section>

        <section id="compatibility-score-card-section" className="page-section" aria-labelledby="score-title" tabIndex="-1">
          <div className="supporting-section-heading">
            <p className="eyebrow">Яснота с един поглед</p>
            <h2 id="score-title">Карта на съвместимостта</h2>
            <p>Използвай оценките като контекст за разговор, а не като заместител на истинското опознаване.</p>
          </div>
          <table aria-label="Примерни оценки за съвместимост">
            <tbody>
              <tr><td><strong>Име 1</strong></td><td><strong>Име 2</strong></td><td><strong>Оценка (0-10)</strong></td></tr>
              <tr><td>88%</td><td>92%</td><td>8/10</td></tr>
            </tbody>
          </table>
        </section>

        <section id="closing-cta" className="page-section closing-cta" aria-labelledby="closing-title" tabIndex="-1">
          <article className="closing-cta-content">
            <p className="eyebrow">Следващата връзка започва от теб</p>
            <h2 id="closing-title">Готов/а ли си за нещо повече от първо впечатление?</h2>
            <p>Открий своя стил на свързване, разгледай примерни съвпадения и упражнявай разговори в собствено темпо.</p>
            <div className="closing-actions">
              <button className="btn btn-primary" type="button" aria-label="Започни с личностния тест на Vibra" onClick={() => navigateTo('personality-preview')}>Започни с характера си</button>
              <button className="btn btn-secondary" type="button" aria-label="Разгледай примерни съвпадения във Vibra" onClick={() => navigateTo('match-preview')}>Разгледай съвпадения</button>
            </div>
            <p className="closing-trust"><span aria-hidden="true">18+</span>Само за пълнолетни. Уважението и съгласието са на първо място.</p>
          </article>
        </section>
      </main>
    </div>
  );
};

export default App;
