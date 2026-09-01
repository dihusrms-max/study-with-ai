const fileInput = document.querySelector('#gif-file');
const dropzone = document.querySelector('#dropzone');
const previewFrame = document.querySelector('#preview-frame');
const preview = document.querySelector('#gif-preview');
const replaceFileButton = document.querySelector('#replace-file');
const status = document.querySelector('#file-status');
const settings = document.querySelector('#settings-fieldset');
const exportButton = document.querySelector('#export-button');
const speed = document.querySelector('#speed');
const speedOutput = document.querySelector('#speed-output');
const scale = document.querySelector('#scale');
const scaleOutput = document.querySelector('#scale-output');
const startFrame = document.querySelector('#start-frame');
const endFrame = document.querySelector('#end-frame');
const editorControls = document.querySelector('#editor-controls');

const MAX_FILE_SIZE = 20 * 1024 * 1024;
let previewUrl = null;
let activeFile = null;
let loadAttempt = 0;
let pendingPreviewUrl = null;

function setStatus(message) {
  status.textContent = message;
}

function isGifFile(file) {
  if (!file || typeof file.name !== 'string' || !Number.isFinite(file.size)) {
    return false;
  }

  const mimeType = typeof file.type === 'string' ? file.type.toLowerCase() : '';
  return mimeType === 'image/gif' || file.name.toLowerCase().endsWith('.gif');
}

function resetPreview() {
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
  }

  previewUrl = null;
  activeFile = null;
  preview.removeAttribute('src');
  previewFrame.hidden = true;
  dropzone.hidden = false;
  settings.disabled = true;
  exportButton.disabled = true;
}

function enableEditor(file, url) {
  const oldPreviewUrl = previewUrl;

  previewUrl = url;
  activeFile = file;
  previewFrame.hidden = false;
  dropzone.hidden = true;
  settings.disabled = false;
  exportButton.disabled = false;

  if (oldPreviewUrl && oldPreviewUrl !== url) {
    URL.revokeObjectURL(oldPreviewUrl);
  }

  setStatus(`${file.name} · ${(file.size / 1024 / 1024).toFixed(1)}MB · 테스트 미리보기 준비됨`);
}

function loadGif(file) {
  if (!isGifFile(file)) {
    setStatus('GIF 파일만 선택할 수 있습니다. 파일 형식과 확장자를 확인해 주세요.');
    return;
  }

  if (file.size === 0 || file.size > MAX_FILE_SIZE) {
    setStatus('0MB 초과, 20MB 이하의 GIF 파일을 선택해 주세요.');
    return;
  }

  let nextPreviewUrl;
  try {
    nextPreviewUrl = URL.createObjectURL(file);
  } catch (error) {
    console.error('GIF 미리보기를 만들 수 없습니다.', error);
    setStatus('GIF 미리보기를 만들지 못했습니다. 다른 파일을 선택해 주세요.');
    return;
  }

  if (pendingPreviewUrl) {
    URL.revokeObjectURL(pendingPreviewUrl);
  }

  pendingPreviewUrl = nextPreviewUrl;
  const attempt = ++loadAttempt;
  const previousPreviewUrl = previewUrl;

  const image = new Image();

  image.onload = () => {
    if (attempt !== loadAttempt) {
      URL.revokeObjectURL(nextPreviewUrl);
      return;
    }

    pendingPreviewUrl = null;
    preview.src = nextPreviewUrl;
    enableEditor(file, nextPreviewUrl);
  };

  image.onerror = () => {
    if (attempt !== loadAttempt) {
      URL.revokeObjectURL(nextPreviewUrl);
      return;
    }

    pendingPreviewUrl = null;
    URL.revokeObjectURL(nextPreviewUrl);
    if (!previousPreviewUrl) {
      resetPreview();
    }

    setStatus('GIF 파일을 읽을 수 없습니다. 손상되지 않은 파일을 선택해 주세요.');
  };

  image.src = nextPreviewUrl;
}

fileInput.addEventListener('change', (event) => {
  const file = event.target.files?.[0];
  loadGif(file);
  event.target.value = '';
});

replaceFileButton.addEventListener('click', () => {
  fileInput.value = '';
  fileInput.click();
});

['dragenter', 'dragover'].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add('is-dragging');
  });
});

['dragleave', 'drop'].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove('is-dragging');
  });
});

dropzone.addEventListener('drop', (event) => {
  loadGif(event.dataTransfer?.files?.[0]);
});

speed.addEventListener('input', () => {
  speedOutput.value = `${speed.value}x`;
});

scale.addEventListener('change', () => {
  scaleOutput.value = scale.value === '100' ? '원본' : `${scale.value}%`;
});

editorControls.addEventListener('submit', (event) => {
  event.preventDefault();

  const start = Number(startFrame.value);
  const end = Number(endFrame.value);

  if (!activeFile) {
    setStatus('먼저 GIF 파일을 선택해 주세요.');
    return;
  }

  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end < start) {
    setStatus('구간 값은 0 이상의 정수이며, 끝 값은 시작 값보다 크거나 같아야 합니다.');
    return;
  }

  setStatus('테스트 페이지입니다. GIF 인코딩과 다운로드는 다음 단계에서 연결합니다.');
});

window.addEventListener('beforeunload', () => {
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
  }

  if (pendingPreviewUrl) {
    URL.revokeObjectURL(pendingPreviewUrl);
  }
});
