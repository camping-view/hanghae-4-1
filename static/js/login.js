//로그아웃기능
function logout_out() {
    $.removeCookie('mytoken', {path: '/'});
    alert('로그아웃!')
    window.location.href = "/login"
}

function login(){
    window.location.href="/login"
}

function writeReview(status) {
    if(status='true'){
        window.location.href = "/review/insert"
    }else{
        if(confirm('로그인하시면 리뷰를 쓸수 있습니다.\n 로그인 하시겠습니까?')){
            login()
        }
    }
}
