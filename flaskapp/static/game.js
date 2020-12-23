var uniqId = (function(){
    var i=0;
    return function() {
        return i++;
    }
})();

function init_ui() {
    fetch("/word")
        .then(response => response.json())
        .then(data => init_ui_part2(data));
}

function init_ui_part2(data_json) {
    button_event_dict = {};
    var article_buttons_row = $(".article-buttons-row");
    article_buttons_row.empty();
    
    data_json.article_choices.forEach(function(article) {
        var button = $("<button class=\"btn btn-primary btn-lg btn-block article-button\">der</button>");
        var button_id = uniqId();
        button.html(article);
        button.click(function() {
            article_button_clicked(data_json, button_id);
        });
        var button_div = $("<div class=\"col-md m-2\">");
        button_div.append(button);
        article_buttons_row.append(button_div);
        button_event_dict[button_id] = button;
    });
    
    var word_container = $(".word-display");
    word_container.html(data_json.noun_hyphen);
}

function article_button_clicked(data_json, button_id) {
    var my_button = button_event_dict[button_id];
    if (my_button === undefined) { // button no longer active
        return;
    }
    var my_article = my_button.html();
    
    var correct_article = data_json.article;
    Object.keys(button_event_dict).forEach(function(key) {
        var button = button_event_dict[key];
        button.css("pointer-events", "none");
        button.blur();
        
        var article = button.html();
        if (article === correct_article) {
            button.removeClass("btn-primary");
            button.addClass("btn-success");
        }
    });
    
    if (my_article === correct_article) { // guessed article correct
        audio_success.play();
    } else { // guessed article wrong
        my_button.removeClass("btn-primary");
        my_button.addClass("btn-danger");
        audio_error.play();
    }
    //~ button.removeClass("btn-primary");
    //~ button.addClass("btn-success");
    //~ button.css("pointer-events", "none");
    //~ button.blur();
    
    button_event_dict = {}; // prevent events for other buttons
    
    setTimeout(init_ui, 3000); // fetch new word and reset, after some delay
}

var button_event_dict = {};
var audio_success;
var audio_error;

$(document).ready(function() {
    audio_success = new Audio("sounds/success.mp3");
    audio_error = new Audio("sounds/error.mp3");
    init_ui();
});
