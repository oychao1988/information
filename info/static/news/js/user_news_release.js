function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {

    $(".release_form").submit(function (e) {
        e.preventDefault()
        // TODO 发布完毕之后需要选中我的发布新闻

        $(this).ajaxSubmit({
            url: '/user/news_release',
            type: 'POST',
            headers: {'X-CSRFToken': getCookie('csrf_token')},
            success: function(resp){
                if(resp.errno==0){
                    // 选中索引为6的左边单菜单
                    window.parent.fnChangeMenu(6)
                    // 滚动到顶部
                    window.parent.scrollTo(0, 0)
                }else{
                    console.log(resp.errmsg)
                }
            }
        })
    })
})