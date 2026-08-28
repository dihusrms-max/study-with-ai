const themeToggle = document.querySelector('.theme-toggle');
const themeLabel = document.querySelector('.theme-label');
const storageKey = 'intro-page-theme';

if (themeToggle && themeLabel) {
  function setTheme(theme) {
    const isDark = theme === 'dark';
    document.documentElement.dataset.theme = theme;
    themeToggle.setAttribute('aria-pressed', String(isDark));
    themeToggle.setAttribute('aria-label', isDark ? '라이트 모드로 전환' : '다크 모드로 전환');
    themeLabel.textContent = isDark ? '라이트 모드' : '다크 모드';
  }

  let savedTheme = null;

  try {
    savedTheme = localStorage.getItem(storageKey);
  } catch {
    // 로컬 파일 또는 개인정보 보호 설정에서 저장소 사용이 차단될 수 있습니다.
  }

  setTheme(savedTheme ?? 'dark');

  themeToggle.addEventListener('click', () => {
    const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);

    try {
      localStorage.setItem(storageKey, nextTheme);
    } catch {
      // 테마 전환은 저장소를 사용할 수 없어도 현재 페이지에서는 동작합니다.
    }
  });
}
