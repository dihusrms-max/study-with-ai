const fileInput = document.querySelector('#gif-file');
const dropzone = document.querySelector('#dropzone');
const previewFrame = document.querySelector('#preview-frame');
const preview = document.querySelector('#gif-preview');
const status = document.querySelector('#file-status');
const settings = document.querySelector('#settings-fieldset');
const exportButton = document.querySelector('#export-button');
const speed = document.querySelector('#speed');
const speedOutput = document.querySelector('#speed-output');
const scale = document.querySelector('#scale');
const scaleOutput = document.querySelector('#scale-output');

let previewUrl = null;

function setStatus(message) { status.textContent = message; }

function loadGif(file) {
  if (!file || file.type !== 'image/gif') { setStatus('GIF 형식의 파일만 선택할 수 있습니다.'); return; }
  if (file.size > 20 * 1024 * 1024) { setStatus('20MB 이하의 GIF를 선택해 주세요.'); return; }
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  preview.src = previewUrl;
  previewFrame.hidden = false;
  dropzone.hidden = true;
  settings.disabled = false;
  exportButton.disabled = false;
  setStatus(`${file.name} · ${(file.size / 1024 / 1024).toFixed(1)}MB · 테스트 미리보기 준비됨`);
}

fileInput.addEventListener('change', () => loadGif(fileInput.files[0]));
['dragenter', 'dragover'].forEach((eventName) => dropzone.addEventListener(eventName, (event) => { event.preventDefault(); dropzone.classList.add('is-dragging'); }));
['dragleave', 'drop'].forEach((eventName) => dropzone.addEventListener(eventName, (event) => { event.preventDefault(); dropzone.classList.remove('is-dragging'); }));
dropzone.addEventListener('drop', (event) => loadGif(event.dataTransfer.files[0]));
speed.addEventListener('input', () => { speedOutput.value = `${speed.value}×`; });
scale.addEventListener('change', () => { scaleOutput.value = scale.value === '100' ? '원본' : `${scale.value}%`; });
document.querySelector('#editor-controls').addEventListener('submit', (event) => { event.preventDefault(); setStatus('테스트 페이지입니다. GIF 인코딩과 다운로드는 아직 연결되지 않았습니다.'); });
window.addEventListener('beforeunload', () => { if (previewUrl) URL.revokeObjectURL(previewUrl); });
