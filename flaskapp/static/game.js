function uniqId() {
  // Math.random should be unique because of its seeding algorithm.
  // Convert it to base 36 (numbers + letters), and grab the first 9 characters
  // after the decimal.
  return Math.random().toString(26).substr(2, 9);
};

function init_ui() {
    toggle_progress_confirm(false);
    // wait a little before updating the progress bar
    // if this is not done, after a wrong word the progress bar change will not be animated
    setTimeout(update_progressbar, 10);
    
    if (words_done == words_total) {
        $(".cancel-button").addClass("invisible");
        setTimeout(exit_game, 1000);
    } else {
        fetch("/word")
            .then(response => response.json())
            .then(data => init_ui_part2(data));
    }
}

function exit_game() {
    var report_url = "/report/" + game_id;
    $.redirect(report_url, {"data": JSON.stringify(answers_list)});
}

function confirm_exit_game() {
    
}

function toggle_progress_confirm(confirm) {
    if (confirm) {
        $(".progress-bar-row").addClass("d-none");
        $(".confirm-button-row").removeClass("d-none");
    } else {
        $(".progress-bar-row").removeClass("d-none");
        $(".confirm-button-row").addClass("d-none");
    }
}

function update_progressbar() {
    var percentage = Math.round(100 * words_done / words_total);
    $(".progress-bar").css("width", percentage.toString() + "%");
}

function init_ui_part2(data_json) {
    data_json_stored = data_json;
    
    button_event_dict = {};
    var article_buttons_row = $(".article-button-row");
    article_buttons_row.empty();
    
    data_json.article_choices.forEach(function(article) {
        var button = $("<button class=\"btn btn-lg m-2 flex-grow-1 btn-primary\"></button>");
        var button_id = uniqId();
        button.html(article);
        button.click(function() {
            article_button_clicked(data_json, button_id);
        });
        article_buttons_row.append(button);
        button_event_dict[button_id] = button;
    });
    
    var word_row = $(".word-row");
    word_row.html(data_json.noun_hyphen);
}

function article_button_clicked(data_json, button_id) {
    var my_button = button_event_dict[button_id];
    if (my_button === undefined) { // button no longer active
        return;
    }
    
    words_done++;
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
    
    var report_item = {"noun" : data_json.noun, "noun_hyphen" : data_json.noun_hyphen,
            "correctArticle" : correct_article,  "guessedArticle" : my_article};
    answers_list.push(report_item);
    
    var word_result = {"gameId" : game_id, "correct" : (my_article === correct_article)};
    fetch("/word-result", {"method" : "post", "headers" : {"Content-Type": "application/json"}, "body": JSON.stringify(word_result)});
    
    if (my_article === correct_article) { // guessed article is correct
        audio_success.play();
        // fetch new word and reset automatically
        if (words_done == words_total) {
            init_ui();
        } else {
            setTimeout(init_ui, 1000);
        }
    } else { // guessed article is wrong
        my_button.removeClass("btn-primary");
        my_button.addClass("btn-danger");
        audio_error.play();
        // fetch new word after manual confirmation
        toggle_progress_confirm(true);
    }
    
    button_event_dict = {}; // prevent events for other buttons
}

var button_event_dict = {};
var audio_success;
var audio_error;
var words_done = 0;
var words_total = 3;
var answers_list = [];
var game_id;
var data_json_stored;

$(document).ready(function() {
    audio_success = new Audio("/static/sounds/success.mp3");
    audio_error = new Audio("/static/sounds/error.mp3");
    game_id = uniqId();
    console.log("game id: " + game_id);
    
    // should only register this once for the persistent button to prevent multiple inits!
    $(".confirm-button").click(function() {
        init_ui();
    });
    
    init_ui();
});
