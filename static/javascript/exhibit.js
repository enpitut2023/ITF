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
  // 入力フィールドの要素を取得
  var moneyInput = document.getElementById("moneyInput");

  // 入力フィールドの入力が変更されたときに呼び出される関数を定義
  moneyInput.oninput = function() {
    // 入力された値を取得
    var inputValue = moneyInput.value;

    // 数字以外の文字を取り除いて、数字だけ残す
    var numericValue = inputValue.replace(/[^0-9]/g, "");

    // 数字以外の文字が入力された場合は、入力フィールドの値を数字だけの値に置き換える
    if (inputValue !== numericValue) {
      moneyInput.value = numericValue;
    }
  };
