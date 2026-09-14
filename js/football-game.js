const canvas = document.querySelector('#game-canvas');
const context = canvas.getContext('2d');
const scoreElement = document.querySelector('#score');
const timeElement = document.querySelector('#time');
const startButton = document.querySelector('#start');
const restartButton = document.querySelector('#restart');
const startScreen = document.querySelector('#start-screen');

const field = { width: canvas.width, height: canvas.height, goalTop: 165, goalBottom: 335 };
const keys = new Set();
let animationFrame;
let startedAt;
let playing = false;
let score = 0;
let player;
let ball;
let keeper;

function resetPositions() {
  player = { x: 170, y: field.height / 2, radius: 22, speed: 4.4 };
  ball = { x: 315, y: field.height / 2, radius: 12, vx: 0, vy: 0 };
  keeper = { x: 735, y: field.height / 2, radius: 24, direction: 1 };
}

function drawCircle(x, y, radius, color, stroke = null) {
  context.beginPath(); context.arc(x, y, radius, 0, Math.PI * 2); context.fillStyle = color; context.fill();
  if (stroke) { context.lineWidth = 3; context.strokeStyle = stroke; context.stroke(); }
}

function drawField() {
  context.clearRect(0, 0, field.width, field.height);
  context.fillStyle = '#14644f'; context.fillRect(0, 0, field.width, field.height);
  context.fillStyle = 'rgba(255,255,255,0.035)';
  for (let x = 0; x < field.width; x += 100) context.fillRect(x, 0, 50, field.height);
  context.strokeStyle = 'rgba(255,255,255,0.86)'; context.lineWidth = 4; context.strokeRect(25, 25, field.width - 50, field.height - 50);
  context.beginPath(); context.arc(field.width / 2, field.height / 2, 72, 0, Math.PI * 2); context.stroke();
  context.strokeRect(665, field.goalTop, 110, field.goalBottom - field.goalTop);
  context.fillStyle = 'rgba(131,240,210,0.2)'; context.fillRect(775, field.goalTop, 25, field.goalBottom - field.goalTop);
}

function drawPlayers() {
  drawCircle(player.x, player.y, player.radius, '#a89cff', '#f4f2ff');
  context.fillStyle = '#171324'; context.font = 'bold 16px Instrument Sans, sans-serif'; context.textAlign = 'center'; context.fillText('YOU', player.x, player.y + 5);
  drawCircle(keeper.x, keeper.y, keeper.radius, '#ff94c9', '#f4f2ff');
  drawCircle(ball.x, ball.y, ball.radius, '#f7f5e8', '#21212a');
}

function movePlayer() {
  let dx = 0; let dy = 0;
  if (keys.has('ArrowUp') || keys.has('w')) dy -= 1;
  if (keys.has('ArrowDown') || keys.has('s')) dy += 1;
  if (keys.has('ArrowLeft') || keys.has('a')) dx -= 1;
  if (keys.has('ArrowRight') || keys.has('d')) dx += 1;
  if (dx || dy) { const length = Math.hypot(dx, dy); player.x += (dx / length) * player.speed; player.y += (dy / length) * player.speed; }
  player.x = Math.max(50, Math.min(650, player.x)); player.y = Math.max(50, Math.min(field.height - 50, player.y));
}

function updateBall() {
  const dx = ball.x - player.x; const dy = ball.y - player.y; const distance = Math.hypot(dx, dy);
  if (distance < player.radius + ball.radius + 4) { const safeDistance = Math.max(distance, 1); ball.vx += (dx / safeDistance) * 1.5; ball.vy += (dy / safeDistance) * 1.5; }
  ball.x += ball.vx; ball.y += ball.vy; ball.vx *= 0.985; ball.vy *= 0.985;
  if (ball.y < 38 || ball.y > field.height - 38) { ball.vy *= -0.78; ball.y = Math.max(38, Math.min(field.height - 38, ball.y)); }
  if (ball.x < 38) { ball.vx *= -0.78; ball.x = 38; }
  if (ball.x > field.width - ball.radius && ball.y > field.goalTop && ball.y < field.goalBottom) { score += 1; scoreElement.textContent = score; resetPositions(); return; }
  if (ball.x > field.width - 38) { ball.vx *= -0.78; ball.x = field.width - 38; }
}

function updateKeeper() {
  keeper.y += keeper.direction * 2.2;
  if (keeper.y < field.goalTop + keeper.radius || keeper.y > field.goalBottom - keeper.radius) keeper.direction *= -1;
  const dx = ball.x - keeper.x; const dy = ball.y - keeper.y;
  if (Math.hypot(dx, dy) < keeper.radius + ball.radius) { ball.vx = -Math.abs(ball.vx || 3.5); ball.vy += dy * 0.12; }
}

function frame(now) {
  if (!playing) return;
  const remaining = Math.max(0, 30 - Math.floor((now - startedAt) / 1000));
  timeElement.textContent = remaining;
  if (remaining === 0) { playing = false; startScreen.hidden = false; startScreen.querySelector('p').textContent = `게임 종료 · ${score}골 성공!`; startButton.textContent = '다시 도전'; return; }
  movePlayer(); updateBall(); updateKeeper(); drawField(); drawPlayers(); animationFrame = requestAnimationFrame(frame);
}

function startGame() { cancelAnimationFrame(animationFrame); score = 0; scoreElement.textContent = score; timeElement.textContent = '30'; resetPositions(); startedAt = performance.now(); playing = true; startScreen.hidden = true; animationFrame = requestAnimationFrame(frame); }

document.addEventListener('keydown', (event) => { if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'w', 'a', 's', 'd'].includes(event.key)) { event.preventDefault(); keys.add(event.key); } });
document.addEventListener('keyup', (event) => keys.delete(event.key));
document.querySelectorAll('[data-key]').forEach((button) => { button.addEventListener('pointerdown', () => keys.add(button.dataset.key)); ['pointerup', 'pointerleave', 'pointercancel'].forEach((eventName) => button.addEventListener(eventName, () => keys.delete(button.dataset.key))); });
startButton.addEventListener('click', startGame); restartButton.addEventListener('click', startGame);
resetPositions(); drawField(); drawPlayers();
