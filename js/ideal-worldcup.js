const candidates = [
  { title: '다정한 대화가 좋은 사람', tag: 'WARM TALKER', description: '사소한 이야기에도 귀 기울이며 편안한 시간을 만드는 스타일', symbol: '☁', colors: ['#4d4a89', '#a89cff'] },
  { title: '취미를 함께 즐기는 사람', tag: 'HOBBY PARTNER', description: '새로운 경험과 좋아하는 일을 함께 나누는 스타일', symbol: '✦', colors: ['#176d65', '#83f0d2'] },
  { title: '자신만의 목표가 있는 사람', tag: 'GOAL GETTER', description: '자신의 길을 꾸준히 걸으며 서로를 응원하는 스타일', symbol: '↗', colors: ['#7d3d72', '#ed9bcb'] },
  { title: '유쾌한 에너지가 있는 사람', tag: 'BRIGHT ENERGY', description: '평범한 순간도 즐겁게 만드는 긍정적인 스타일', symbol: '☀', colors: ['#b0602c', '#ffc777'] },
  { title: '차분한 여유가 있는 사람', tag: 'CALM MIND', description: '서두르지 않고 서로의 속도를 존중하는 스타일', symbol: '◌', colors: ['#285a75', '#83b8df'] },
  { title: '솔직한 마음을 표현하는 사람', tag: 'HONEST HEART', description: '생각과 감정을 진심으로 나누는 스타일', symbol: '♡', colors: ['#8c395f', '#f19ac2'] },
  { title: '센스 있는 취향을 가진 사람', tag: 'GOOD TASTE', description: '음악과 영화, 일상 속의 취향을 함께 발견하는 스타일', symbol: '♫', colors: ['#4b377c', '#c1a7ff'] },
  { title: '든든하게 믿을 수 있는 사람', tag: 'STEADY ONE', description: '언제나 같은 자리에서 힘이 되어 주는 스타일', symbol: '◆', colors: ['#336b56', '#a2d8b3'] },
];

const matchup = document.querySelector('#matchup');
const roundLabel = document.querySelector('#round-label');
const matchCount = document.querySelector('#match-count');
const progressBar = document.querySelector('#progress-bar');
const matchHint = document.querySelector('#match-hint');
const worldcupCard = document.querySelector('.worldcup-card');
const resultCard = document.querySelector('#result-card');
const winnerVisual = document.querySelector('#winner-visual');
const winnerTitle = document.querySelector('#winner-title');
const winnerDescription = document.querySelector('#winner-description');
const restartButton = document.querySelector('#restart');

let currentRound = [];
let nextRound = [];
let matchIndex = 0;
let completedMatches = 0;

function shuffle(items) { return [...items].sort(() => Math.random() - 0.5); }
function roundName(size) { return `${size}강`; }

function candidateMarkup(candidate) {
  const style = `--color-a:${candidate.colors[0]};--color-b:${candidate.colors[1]};`;
  return `<button class="candidate" type="button" style="${style}" data-title="${candidate.title}"><div class="candidate-visual"><span class="candidate-symbol">${candidate.symbol}</span></div><div class="candidate-copy"><span>${candidate.tag}</span><h2>${candidate.title}</h2><p>${candidate.description}</p></div></button>`;
}

function renderMatch() {
  const first = currentRound[matchIndex];
  const second = currentRound[matchIndex + 1];
  const total = currentRound.length / 2;
  roundLabel.textContent = roundName(currentRound.length);
  matchCount.textContent = `${matchIndex / 2 + 1} / ${total}`;
  progressBar.style.width = `${(completedMatches / 7) * 100}%`;
  matchup.innerHTML = `${candidateMarkup(first)}<span class="versus">VS</span>${candidateMarkup(second)}`;
  matchup.querySelectorAll('.candidate').forEach((button, index) => button.addEventListener('click', () => choose(index === 0 ? first : second)));
}

function choose(winner) {
  nextRound.push(winner); completedMatches += 1; matchIndex += 2;
  if (matchIndex < currentRound.length) { renderMatch(); return; }
  if (nextRound.length === 1) { showResult(nextRound[0]); return; }
  currentRound = nextRound; nextRound = []; matchIndex = 0; renderMatch();
}

function showResult(winner) {
  const style = `--color-a:${winner.colors[0]};--color-b:${winner.colors[1]};`;
  winnerVisual.setAttribute('style', style);
  winnerVisual.innerHTML = `<span class="candidate-symbol">${winner.symbol}</span>`;
  winnerTitle.textContent = winner.title;
  winnerDescription.textContent = winner.description;
  progressBar.style.width = '100%';
  matchHint.textContent = '나만의 이상형 스타일을 찾았습니다.';
  worldcupCard.hidden = true;
  resultCard.hidden = false;
}

function startWorldCup() {
  currentRound = shuffle(candidates); nextRound = []; matchIndex = 0; completedMatches = 0;
  resultCard.hidden = true; worldcupCard.hidden = false; renderMatch();
}

restartButton.addEventListener('click', startWorldCup);
startWorldCup();
