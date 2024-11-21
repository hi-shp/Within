function toggleLanguage() {
    const button = document.getElementById('lang-toggle-button');
    const isEnglish = button.innerText === 'Kor';

    // 버튼 텍스트 변경
    button.innerText = isEnglish ? 'Eng' : 'Kor';

    // 페이지 텍스트 변경
    const elements = document.querySelectorAll('[data-lang-eng]');
    elements.forEach((el) => {
        el.innerHTML = isEnglish ? el.getAttribute('data-lang-kor') : el.getAttribute('data-lang-eng');
    });

    // 로컬 스토리지에 언어 저장
    const newLang = isEnglish ? 'kor' : 'eng';
    localStorage.setItem('language', newLang);

    // 알림 표시
    alert(isEnglish ? '한글로 변경됩니다.' : '영어로 변경됩니다.');
}

document.addEventListener("DOMContentLoaded", function () {
    // 로컬 스토리지에서 저장된 언어 가져오기
    const savedLang = localStorage.getItem('language') || 'kor';
    const button = document.getElementById('lang-toggle-button');

    // 언어에 따라 버튼 텍스트와 페이지 텍스트 변경
    button.innerText = savedLang === 'kor' ? 'Eng' : 'Kor';
    const elements = document.querySelectorAll('[data-lang-eng]');
    elements.forEach((el) => {
        el.innerHTML = savedLang === 'kor' ? el.getAttribute('data-lang-kor') : el.getAttribute('data-lang-eng');
    });
});
