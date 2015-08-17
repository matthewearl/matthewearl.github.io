
var reddit_scores = (function () {
    var fetch = function() {
        var id = ("t3_" +
                  document.getElementById('reddit-url').href.split('/')[6]);
        var url = "//www.reddit.com/api/info.json?id=" + id;
        var req = new XMLHttpRequest();
        var on_json_get = function(parsed) {
            var score = parsed["data"]["children"][0]["data"]["score"];
            var num_comments =
                         parsed["data"]["children"][0]["data"]["num_comments"];
            var text = "(" + score + " points / " +
                            num_comments + " comments)";
            var divs = document.getElementsByClassName('reddit-score');
            
            for (var i = 0; i < divs.length; i++) {
                var div = divs[i];
                while (div.firstChild) {
                    div.removeChild(div.firstChild);
                }
                div.appendChild(document.createTextNode(text));
            }
        }
        req.onreadystatechange = function() {
            if (req.readyState == 4 && req.status == 200) {
                var parsed = JSON.parse(req.responseText);
                on_json_get(parsed);
            }
        }
        req.open("get", url, true);
        req.send();
    }

    return {
        'fetch': fetch,
    }
})();

