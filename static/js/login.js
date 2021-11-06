//로그아웃시 토큰 삭제
function logout_out() {
    $.removeCookie('mytoken', {path: '/'});
    alert('로그아웃!')
    window.location.href = "/login"
}

//로그인 페이지 가기
function login(){
    window.location.href="/login"
}

//리뷰 작성 페이지 가기
function writeReview(status) {
    if(status='true'){
        window.location.href = "/review/insert"
    }else{
        if(confirm('로그인하시면 리뷰를 쓸수 있습니다.\n 로그인 하시겠습니까?')){
            login()
        }
    }
}
