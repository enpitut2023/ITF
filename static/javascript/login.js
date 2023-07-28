document.getElementById('login-form').addEventListener('submit', function (e) {
    e.preventDefault();

    var username = document.getElementById('user-name').value;
    var password = document.getElementById('login-password').value;

    fetch('/receive_username', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username
        })
    })
        .then(response => response.json())
        .then(data => {
            console.log(data);  // 全てのレスポンスデータをログに出力
            email = data.email;  // レスポンスデータからemailフィールドの値を取得
            console.log(email);  // emailの値をログに出力
        })
        .catch((error) => {
            console.error('Error:', error);
        });


    firebase.auth().signInWithEmailAndPassword(email, password)
        .then((userCredential) => {
            // ログイン成功
            var user = userCredential.user;
            alert("ログイン成功");
        })
        .catch((error) => {
            // ログイン失敗
            var errorCode = error.code;
            var errorMessage = error.message;
            alert("ログイン失敗: " + errorMessage);
        });
});
