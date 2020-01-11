let parseQs = function(qs) {
    let obj = {};
    if (qs.length === 0) {
      return obj;
    }

    let params = qs.replace(/\+/g,' ').split('&');
    for (x of params) {
         let idx = x.indexOf("=");
         if (idx >= 0) {
            kstr = x.substring(0, idx);
            vstr = x.substring(idx + 1);
        } else {
            kstr = x;
            vstr = '';
        }

        k = decodeURIComponent(kstr);
        v = decodeURIComponent(vstr);

        obj[k] = v;
    }
    return obj;
};

// read the session id from the query string
const params = parseQs(window.location.search.substring(1));
document.getElementById("field-session_id").value = params["session_id"];

let inputField = document.getElementById("field-username");
let inputForm = document.getElementById("form");
let submitButton = document.getElementById("button-submit");
let message = document.getElementById("message");

// Remove input field placeholder if the text field is not empty
let switchClass = function(input) {
  if (input.value.length > 0) {
    input.classList.add('has-contents');
  }
  else {
    input.classList.remove('has-contents');
  }
};

// Submit username and receive response
let showMessage = function(messageText) {
  // Unhide the message text
  message.classList.remove("hidden");

  message.innerHTML = messageText;
};

let onResponse = function(response, success) {
  // Display message
  showMessage(response);

  if(success) {
    inputForm.submit();
    return;
  }

  // Enable submit button and input field
  submitButton.classList.remove('button--disabled');
  submitButton.value = "Submit"
};

// We allow upper case characters here, but then lowercase before sending to the server
let allowedUsernameCharacters = RegExp("[^a-zA-Z0-9\\.\\_\\=\\-\\/]");
let usernameIsValid = function(username) {
  return !allowedUsernameCharacters.test(username);
}
let allowedCharactersString = "" +
"<code>a-z</code>, " +
"<code>0-9</code>, " +
"<code>.</code>, " +
"<code>_</code>, " +
"<code>-</code>, " +
"<code>/</code>, " +
"<code>=</code>";

var dummyBool = false;
let submitUsername = function(username) {
  if(username.length == 0) {
    onResponse("Please enter a username.", false);
    return;
  }
  if(!usernameIsValid(username)) {
    onResponse("Invalid username. Only the following characters are allowed: " + allowedCharactersString, false);
    return;
  }
  setTimeout(() => {
    if(dummyBool) {
      onResponse("This username is not available, please choose another.", false);
    } else {
      onResponse("Success. Please wait a moment for your browser to redirect.", true);
    }
  }, 750);
}

let clickSubmit = function() {
  if(submitButton.classList.contains('button--disabled')) { return; }

  // Disable submit button and input field
  submitButton.classList.add('button--disabled');

  // Submit username
  submitButton.value = "Checking...";
  submitUsername(inputField.value);
};

submitButton.onclick = clickSubmit;

// Listen for events on inputField
inputField.addEventListener('keypress', function(event) {
  // Listen for Enter on input field
  if(event.which === 13) {
    event.preventDefault();
    clickSubmit();
    return true;
  }
  switchClass(inputField);
});
inputField.addEventListener('change', function() {
  switchClass(inputField);
});

