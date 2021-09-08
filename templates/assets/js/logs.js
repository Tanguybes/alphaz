
function onReady(callback) {
  var intervalId = window.setInterval(function() {
    if (document.getElementsByTagName('body')[0] !== undefined) {
      window.clearInterval(intervalId);
      callback.call(this);
    }
  }, 1000);
}

function setVisible(selector, visible) {
    var el = document.querySelector(selector);
    if (el != undefined) {
        el.style.display = visible ? 'block' : 'none';
    }
}

function getLogFileContent(id, name, node, opened, force) {
    //$(window).scrollTop(0);
    setVisible('#loading', true);

    var element = $("#"+id)[0];
    var element_state = (element != undefined) ? element.style.display: '';

    //if ($("#"+name)[0] && $("#"+name)[0].style.display == "block") {

    var request = "name=" + name + "&node=" + node + "&content=Y";
    
    if(name != undefined && node != undefined && (element_state == '' || force)) {
        $.ajax({
            type: "GET",
            url: "/logs/file",
            data: request,
            success: function(data, status) {
              //location.reload();
              var ansi_up = new AnsiUp;

              var content = data.data['content']
              var html_raw = ansi_up.ansi_to_html(content);

              html_raw = html_raw.replace(/(?:\r\n|\r|\n)/g, '<br>');

              var html = "";
              html_split = html_raw.split('<br>');
              
              var blocks = [];
              var block = undefined;

              const startDateStr = $("#start-date")[0].value
              const endDateStr = $("#end-date")[0].value

              const gunicorn = name.includes("gunicorn")
              const beat = name.includes("beat")
              const worker = name.includes("worker")

              var regexp = "[0-9]{4}-[0-9]{2}-[0-9]{2}\\s[0-9]{2}:[0-9]{2}:[0-9]{2}\\s-";
              var regexp_unicorn = "[0-9]{2}\/[a-zA-Z]+\/[0-9]{4}:[0-9]{2}:[0-9]{2}:[0-9]{2}";
              var regexp_beat = "[0-9]{4}-[0-9]{2}-[0-9]{2}\\s[0-9]{2}:[0-9]{2}:[0-9]{2}";

              var regex_start = RegExp(regexp, )
              var regex_start_gunicorn = RegExp(regexp_unicorn, )
              var regex_start_beat = RegExp(regexp_beat, )

              for(var i in html_split) {
                var line = html_split[i];
                var new_line = regex_start.test(line) || regex_start_gunicorn.test(line) || regex_start_beat.test(line);

                if (new_line && block == undefined) {
                  var values = undefined;
                  var date_str = undefined;
                    if (gunicorn){
                      values = [...line.matchAll(regexp_unicorn)];
                      date_str = values[0];
                    } else if (beat || worker){
                      values = [...line.matchAll(regexp_beat)];
                      date_str = values[0];
                    }else {
                      values = [...line.matchAll(regexp)];
                      date_str = values[0][0].split(' -')[0];
                    }
                    const date = Date.parse(date_str);

                    if (startDateStr != "") {
                      startDate = Date.parse(startDateStr)
                      if (date < startDate) new_line = false;
                    }

                    if (endDateStr != "") {
                      endDate = Date.parse(endDateStr)
                      if (date > endDate) new_line = false;
                    }

                    if (new_line) block = line;
                } else if (new_line && block != undefined) {
                    blocks.push(block);
                    block = undefined;
                } else if (block != undefined) 
                    block += '<br>' + line
              }
              if (block != undefined) blocks.push(block);

              var debug_string = (beat || worker) ? "DEBUG/" : '- DEBUG ';
              var info_string = (beat || worker) ? "INFO/" : '- INFO ';
              var warning_string = (beat || worker) ? "DEBUG/" : '- DEBUG ';
              var error_string = (beat || worker) ? "DEBUG/" : '- DEBUG ';

              if (!document.getElementById('debug').checked)
                blocks = blocks.filter(line => line.indexOf(debug_string) === -1);
              if (!document.getElementById('info').checked)
                blocks = blocks.filter(line => line.indexOf(info_string) === -1);
              if (!document.getElementById('warning').checked)
                blocks = blocks.filter(line => line.indexOf(warning_string) === -1);
              if (!document.getElementById('error').checked)
                blocks = blocks.filter(line => line.indexOf(error_string) === -1);

              var search = document.getElementById('search').value;
              var regex_search = RegExp(search, )
              if (search != undefined && search != "")
                blocks = blocks.filter(line => regex_search.test(line));

              html = blocks.join('<br><hr>')

              html = html.replaceAll(debug_string, '- <span class="debug">DEBUG</span> ');
              html = html.replaceAll(info_string, '- <span class="info">INFO</span> ');
              html = html.replaceAll(warning_string, '- <span class="warning">WARNING</span> ');
              html = html.replaceAll(error_string, '- <span class="error">ERROR</span> ');
            
              $("#" + id).html(html);
              var element = $("#" + id)[0];
              if (opened != undefined && opened && element)
                $("#" + id).scrollTop(element.scrollHeight);

              setVisible('#loading', false);
            },
            error: function (err) { console.log(err); setVisible('#loading', false); }
          });
    } else {
        setVisible('#loading', false);
    }
  }

  onReady(function() {
  setVisible('#loading', false);
});

var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function() {

    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if(content != undefined) {
        if (content.style.display === "block") {
        content.style.display = "none";
        } else {
        content.style.display = "block";
        }
    }
  });
}

function checkContents(force) {
    $(".content").map(x=> {
        var name = $(".content")[x].id;

        if ($("#"+name)[0] && $("#"+name)[0].style.display == "block") {
            console.log('Reload',name);
            getLogFileContent(name, $("#"+name)[0].classList[1], $("#"+name)[0].classList[2], false, force);
        }
    })
}

setInterval(function(){ 
    //this code runs every second 
    //checkContents();
}, 10000);

function onClickHandler(name){    
    if(!document.getElementById(name).checked) localStorage.setItem(name, true);
    else localStorage.removeItem(name);

    checkContents(true);
}

var levels = ['debug','info','warning','error','critical'];
for(var i in levels)
{
    var stor = localStorage.getItem(levels[i]);
    if(stor != undefined && stor) {
      var el = document.getElementById(levels[i]);
      if (el != undefined) el.checked = false;
    }
}

function dateChange() {
  checkContents(true);
}