
var reddit_scores = (function () {
    function reddit_url_div_to_id(div, _) {
        var out = "t3_" + $(div).attr("href").split('/')[6];
        if ($(div).children(".reddit-score").attr("data-fetched") == 0) {
            return out;
        }
    }

    function update_divs(details) {
        $.each(
            $(".reddit-url"),
            function(idx, div) {
                var id = reddit_url_div_to_id(div);
                if (id in details) {
                    $(div).children(".reddit-score")
                          .text("(" + details[id].score + " points / " +
                                details[id].num_comments + " comments)")
                          .attr("data-fetched", "1");
                }
            });
    }

    var fetch = function() {
        var ids = $.map($(".reddit-url"), reddit_url_div_to_id).join(",");
        if (ids.length > 0) {
            var url = "//www.reddit.com/api/info.json?id=" + ids;
            $.ajax(url, {"method": "get", "dataType": "json"}).done(
              function (d) {
                var details = new Object()
                $.each(d["data"]["children"],
                       function(i, el) {
                           details["t3_" + el["data"]["id"]] = {
                                  "score": el["data"]["score"],
                                  "num_comments": el["data"]["num_comments"],
                           }
                       });
                update_divs(details);
              }
            );
        }
    }

    return {
        'fetch': fetch,
    }
})();

