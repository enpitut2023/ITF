function showAlert() {
  alert('出品しました！');
}

  const checkboxes = document.querySelectorAll('input[type="checkbox"]');

  function validateCheckBoxes() {
    let checkedCount = 0;
    checkboxes.forEach(checkbox => {
      if (checkbox.checked) {
        checkedCount++;
      }
    });

    if (checkedCount === 0) {
      alert('最低でも一つの項目を選択してください。');
      return false;
    }
    showAlert()
    return true;

  }

  const form = document.querySelector('form');

  form.addEventListener('submit', function(event) {
    if (!validateCheckBoxes()) {
      event.preventDefault();
      
    }
  });

